from datetime import datetime
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from django.http import HttpResponse
from django.utils.timezone import now
from django_hosts import reverse
from waffle.testutils import override_flag

from config.hosts import PUBLISH_HOST
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.data_quality.report_summary import Summary
from transit_odp.dqs.constants import ReportStatus
from transit_odp.dqs.factories import ReportFactory
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.pipelines.factories import DataQualityTaskFactory
from transit_odp.pipelines.models import DataQualityTask
from transit_odp.users.constants import AgentUserType, OrgAdminType
from transit_odp.users.factories import AgentUserInviteFactory, UserFactory
from transit_odp.users.models import AgentUserInvite

pytestmark = pytest.mark.django_db


@pytest.fixture
def timetable_status_request(client_factory):
    user = UserFactory(account_type=OrgAdminType)
    revision = DatasetRevisionFactory(
        dataset__organisation=user.organisations.first(),
        dataset__dataset_type=TimetableType,
        is_published=False,
    )
    url = reverse(
        "nextjs-timetables-data-quality-status",
        host=PUBLISH_HOST,
        kwargs={"pk1": revision.dataset.organisation_id, "pk": revision.dataset_id},
    )
    return client_factory(host=PUBLISH_HOST), user, revision, url


@pytest.mark.parametrize(
    "report_status, expected",
    [
        (None, "PENDING"),
        (ReportStatus.PIPELINE_PENDING.value, "PENDING"),
        (ReportStatus.REPORT_GENERATED.value, "SUCCESS"),
        (ReportStatus.REPORT_GENERATION_FAILED.value, "SUCCESS"),
    ],
)
@override_flag("is_new_data_quality_service_active", active=True)
def test_timetable_data_quality_status_for_new_service(
    timetable_status_request, report_status, expected
):
    client, user, revision, url = timetable_status_request
    if report_status is not None:
        ReportFactory(revision=revision, status=report_status)

    client.force_login(user)
    response = client.get(url)

    assert response.status_code == 200
    assert response.json() == expected


@override_flag("is_new_data_quality_service_active", active=False)
def test_timetable_data_quality_status_for_legacy_service(timetable_status_request):
    client, user, revision, url = timetable_status_request
    client.force_login(user)

    assert client.get(url).json() == "PENDING"
    DataQualityTaskFactory(revision=revision, status=DataQualityTask.FAILURE)
    assert client.get(url).json() == "FAILURE"


def test_timetable_data_quality_status_requires_org_access(timetable_status_request):
    client, _, _, url = timetable_status_request

    assert client.get(url).status_code == 401
    client.force_login(UserFactory(account_type=OrgAdminType))
    assert client.get(url).status_code == 404


@override_flag("is_new_data_quality_service_active", active=True)
def test_timetable_review_status_serialises_numpy_report_counts(
    timetable_status_request,
):
    client, user, revision, _ = timetable_status_request
    revision.status = "success"
    revision.save()
    ReportFactory(revision=revision, status=ReportStatus.REPORT_GENERATED.value)
    url = reverse(
        "nextjs-timetables-review-status",
        host=PUBLISH_HOST,
        kwargs={"pk1": revision.dataset.organisation_id, "pk": revision.dataset_id},
    )
    summary = Summary(
        data={
            "Critical": {"count": np.int64(2)},
            "Advisory": {"count": np.int64(3)},
        },
        count=5,
    )

    client.force_login(user)
    with patch(
        "transit_odp.timetables.views.api.Summary.get_report", return_value=summary
    ):
        response = client.get(url)

    assert response.status_code == 200
    data_quality = response.json()["dataQuality"]
    assert data_quality["status"] == "SUCCESS"
    assert data_quality["criticalCount"] == 2
    assert data_quality["advisoryCount"] == 3
    assert data_quality["hasCriticalIssues"] is True
    assert data_quality["reportId"] == revision.dqs_report.first().id


def _report_url(revision, name="nextjs-timetables-data-quality-report", **kwargs):
    return reverse(
        name,
        host=PUBLISH_HOST,
        kwargs={
            "pk1": revision.dataset.organisation_id,
            "pk": revision.dataset_id,
            **kwargs,
        },
    )


def test_timetable_data_quality_report_serialises_levels(timetable_status_request):
    client, user, revision, _ = timetable_status_request
    report = ReportFactory(
        revision=revision, status=ReportStatus.REPORT_GENERATED.value
    )
    observations = pd.DataFrame(
        [
            {
                "observation": "Incorrect stop type",
                "url": "incorrect-stop-type",
                "number_of_services_affected": np.int64(5),
                "number_of_suppressed_observation": np.int64(2),
            },
            {
                "observation": "Missing journey code",
                "url": "#",
                "number_of_services_affected": np.int64(1),
                "number_of_suppressed_observation": np.int64(0),
            },
        ]
    )
    summary = Summary(
        data={
            "Critical": {"count": np.int64(0), "intro": "Critical intro"},
            "Advisory": {
                "count": np.int64(4),
                "intro": "Advisory intro",
                "df": {"Stops": observations},
            },
        },
        count=4,
        bus_services_affected=np.int64(3),
    )

    client.force_login(user)
    with patch(
        "transit_odp.timetables.views.data_quality_api.Summary.get_report",
        return_value=summary,
    ) as get_report:
        response = client.get(_report_url(revision))

    get_report.assert_called_once_with(report.id, revision.id)
    assert response.status_code == 200
    assert response.json() == {
        "reportId": report.id,
        "title": revision.name,
        "busServicesAffected": 3,
        "hasCriticalIssues": False,
        "levels": [
            {
                "level": "Critical",
                "count": 0,
                "intro": "Critical intro",
                "categories": [],
            },
            {
                "level": "Advisory",
                "count": 4,
                "intro": "Advisory intro",
                "categories": [
                    {
                        "category": "Stops",
                        "count": 4,
                        "suppressedCount": 2,
                        "observations": [
                            {
                                "observation": "Incorrect stop type",
                                "slug": "incorrect-stop-type",
                                "count": 3,
                                "suppressedCount": 2,
                            },
                            {
                                "observation": "Missing journey code",
                                "slug": None,
                                "count": 1,
                                "suppressedCount": 0,
                            },
                        ],
                    }
                ],
            },
        ],
    }


@pytest.mark.parametrize(
    "counts, expected",
    [
        ({"Critical": 1, "Advisory": 0}, True),
        ({"Critical": 0, "Advisory": 3, "Feedback": 1}, True),
        ({"Critical": 0, "Advisory": 3, "Feedback": 0}, False),
    ],
)
def test_timetable_data_quality_report_critical_issues(
    timetable_status_request, counts, expected
):
    client, user, revision, _ = timetable_status_request
    ReportFactory(revision=revision, status=ReportStatus.REPORT_GENERATED.value)
    summary = Summary(
        data={level: {"count": np.int64(count)} for level, count in counts.items()}
    )

    client.force_login(user)
    with patch(
        "transit_odp.timetables.views.data_quality_api.Summary.get_report",
        return_value=summary,
    ):
        response = client.get(_report_url(revision))

    assert response.json()["hasCriticalIssues"] is expected


def test_timetable_data_quality_report_not_found_without_generated_report(
    timetable_status_request,
):
    client, user, revision, _ = timetable_status_request
    ReportFactory(revision=revision, status=ReportStatus.PIPELINE_PENDING.value)

    client.force_login(user)
    response = client.get(_report_url(revision))

    assert response.status_code == 404


def test_timetable_data_quality_report_requires_org_membership(
    timetable_status_request,
):
    client, _, revision, _ = timetable_status_request
    ReportFactory(revision=revision, status=ReportStatus.REPORT_GENERATED.value)

    client.force_login(UserFactory(account_type=OrgAdminType))
    response = client.get(_report_url(revision))

    assert response.status_code in (403, 404)


def test_timetable_data_quality_report_csv_streams_from_s3(timetable_status_request):
    client, user, revision, _ = timetable_status_request
    report = ReportFactory(
        revision=revision,
        status=ReportStatus.REPORT_GENERATED.value,
        file_name="report.csv",
    )
    csv_response = HttpResponse(b"a,b\n1,2\n", content_type="text/csv")
    csv_response["Content-Disposition"] = "attachment; filename=report.csv"

    client.force_login(user)
    with patch(
        "transit_odp.timetables.views.data_quality_api.get_dqs_report_from_s3",
        return_value=csv_response,
    ) as get_from_s3:
        response = client.get(
            _report_url(
                revision,
                name="nextjs-timetables-data-quality-report-csv",
                report_id=report.id,
            )
        )

    get_from_s3.assert_called_once_with("report.csv")
    assert response.status_code == 200
    assert response["Content-Disposition"] == "attachment; filename=report.csv"
    assert response.content == b"a,b\n1,2\n"


def test_timetable_data_quality_report_csv_rejects_other_dataset_report(
    timetable_status_request,
):
    client, user, revision, _ = timetable_status_request
    other_report = ReportFactory(status=ReportStatus.REPORT_GENERATED.value)

    client.force_login(user)
    with patch(
        "transit_odp.timetables.views.data_quality_api.get_dqs_report_from_s3"
    ) as s3:
        response = client.get(
            _report_url(
                revision,
                name="nextjs-timetables-data-quality-report-csv",
                report_id=other_report.id,
            )
        )

    s3.assert_not_called()
    assert response.status_code == 404


class TestPublishReview:
    user_type = OrgAdminType
    host = PUBLISH_HOST

    def setup(self):
        self.user = UserFactory(account_type=self.user_type)
        self.revision = DatasetRevisionFactory(
            dataset__contact=self.user,
            dataset__dataset_type=TimetableType,
            dataset__organisation=self.user.organisations.first(),
            is_published=False,
        )
        DataQualityReportFactory(revision=self.revision)
        self.url = reverse(
            "revision-publish",
            host=self.host,
            kwargs={
                "pk": self.revision.dataset.id,
                "pk1": self.revision.dataset.organisation.id,
            },
        )

    def test_draft_revision_notifies_on_publish(self, client_factory, mailoutbox):
        client = client_factory(host=self.host)
        client.force_login(self.user)

        response = client.post(
            self.url,
            data={
                "consent": "on",
                "submit": "submit",
            },
        )

        fished_out_dataset = Dataset.objects.get(id=self.revision.dataset.id)
        assert response.status_code == 302
        assert fished_out_dataset.live_revision == self.revision
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == "Data set published"

    def test_pti_hardblock_template_is_used_for_drafts_which_fail_pti(
        self, client_factory
    ):
        PTIObservationFactory(revision=self.revision)
        client = client_factory(host=self.host)
        client.force_login(self.user)

        response = client.get(self.url)

        assert response.status_code == 200
        assert "publish/snippets/pti_panel/soft_fail.html" in [
            t.name for t in response.templates
        ]

    def test_form_cant_publish_draft_datasets_which_fail_pti(self, client_factory):
        PTIObservationFactory(revision=self.revision)
        client = client_factory(host=self.host)
        client.force_login(self.user)

        response = client.post(
            self.url,
            data={
                "consent": "on",
                "submit": "submit",
            },
        )

        assert response.status_code == 302

    def test_draft_notifies_on_publish_new_revision(self, client_factory, mailoutbox):
        self.revision.is_published = True
        self.revision.published_by = self.revision.dataset.contact
        self.revision.published_at = now()
        self.revision.save()
        DatasetSubscriptionFactory(dataset=self.revision.dataset)

        DatasetRevisionFactory(
            dataset=self.revision.dataset,
            is_published=False,
        )

        client = client_factory(host=self.host)
        client.force_login(self.user)

        response = client.post(
            self.url,
            data={
                "consent": "on",
                "submit": "submit",
            },
        )

        assert response.status_code == 302
        assert len(mailoutbox) == 2
        publisher, developer = mailoutbox
        assert publisher.subject == "Data set published"
        assert developer.subject == "Data set status changed"


class TestPublishReviewByAgent(TestPublishReview):
    user_type = AgentUserType

    def setup(self):
        super().setup()
        AgentUserInviteFactory(
            agent=self.user,
            organisation=self.user.organisations.first(),
            status=AgentUserInvite.ACCEPTED,
        )


def test_old_datasets_use_pti_hardblock_templates(client_factory):
    the_past = datetime(2020, 1, 1)
    user = UserFactory(account_type=OrgAdminType)
    revision = DatasetRevisionFactory(
        dataset__contact=user,
        dataset__dataset_type=TimetableType,
        dataset__organisation=user.organisations.first(),
        dataset__created=the_past,
        dataset__modified=the_past,
        is_published=False,
        created=the_past,
        modified=the_past,
    )
    url = reverse(
        "revision-publish",
        host=PUBLISH_HOST,
        kwargs={
            "pk": revision.dataset.id,
            "pk1": revision.dataset.organisation.id,
        },
    )
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)

    response = client.get(url)

    assert response.status_code == 200
    assert "publish/snippets/pti_panel/pass.html" in [
        t.name for t in response.templates
    ]
