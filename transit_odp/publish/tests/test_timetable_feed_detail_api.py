import datetime
from unittest import mock

import pytest
from django_hosts import reverse
from waffle.testutils import override_flag

from config.hosts import PUBLISH_HOST
from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
    PTIObservationFactory,
)
from transit_odp.dqs.factories import ReportFactory
from transit_odp.organisation.constants import (
    AVLType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
    TXCFileAttributesFactory,
)
from transit_odp.pipelines.factories import DatasetETLErrorFactory
from transit_odp.timetables.tests.test_line_detail_api import (
    LINE_NAME,
    SERVICE_CODE,
    build_line,
)
from transit_odp.users.constants import DeveloperType, OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

DQS_FLAG = "is_new_data_quality_service_active"


@pytest.fixture
def org_user():
    return UserFactory(account_type=OrgAdminType)


@pytest.fixture
def client(client_factory, org_user):
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(org_user)
    return client


@pytest.fixture
def dataset(org_user):
    return DatasetFactory(
        organisation=org_user.organisations.first(),
        dataset_type=TimetableType,
        live_revision__name="Live timetable",
        live_revision__description="Live description",
        live_revision__short_description="Short",
        live_revision__url_link="",
    )


def detail_url(dataset, name="nextjs-timetables-feed-detail"):
    return reverse(
        name,
        host=PUBLISH_HOST,
        kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
    )


def line_url(dataset):
    return detail_url(dataset, "nextjs-timetables-feed-line-detail")


@pytest.mark.parametrize("url_for", [detail_url, line_url])
class TestAccess:
    def test_anonymous_gets_401(self, client_factory, dataset, url_for):
        response = client_factory(host=PUBLISH_HOST).get(url_for(dataset))
        assert response.status_code == 401
        assert response.json() == {"error": "Authentication required"}

    def test_non_org_user_gets_403(self, client_factory, dataset, url_for):
        client = client_factory(host=PUBLISH_HOST)
        client.force_login(UserFactory(account_type=DeveloperType))
        assert client.get(url_for(dataset)).status_code == 403

    def test_other_organisation_gets_403(self, client_factory, dataset, url_for):
        client = client_factory(host=PUBLISH_HOST)
        client.force_login(UserFactory(account_type=OrgAdminType))
        assert client.get(url_for(dataset)).status_code == 403

    def test_unknown_dataset_gets_404(self, client, dataset, url_for):
        url = url_for(dataset).replace(f"/{dataset.id}/", "/999999/")
        assert client.get(url).status_code == 404

    def test_draft_dataset_gets_404(self, client, org_user, url_for):
        draft = DraftDatasetFactory(
            organisation=org_user.organisations.first(), dataset_type=TimetableType
        )
        assert client.get(url_for(draft)).status_code == 404

    def test_other_dataset_type_gets_404(self, client, org_user, url_for):
        avl = DatasetFactory(
            organisation=org_user.organisations.first(), dataset_type=AVLType
        )
        assert client.get(url_for(avl)).status_code == 404


def test_feed_detail_payload_for_live_dataset(client, dataset):
    live_revision = dataset.live_revision
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code="PB0000001:1",
        line_names=["42", "7"],
        national_operator_code="NOC1",
        licence_number="PD0001",
    )

    response = client.get(detail_url(dataset))

    assert response.status_code == 200
    data = response.json()
    assert data["orgId"] == dataset.organisation_id
    assert data["datasetId"] == dataset.id
    assert data["liveRevisionId"] == live_revision.id
    assert data["name"] == "Live timetable"
    assert data["description"] == "Live description"
    assert data["shortDescription"] == "Short"
    assert data["ownerName"] == dataset.organisation.name
    assert data["urlLink"] is None
    assert data["transxchangeVersion"] == "2.4"
    assert data["status"] == "success"
    assert data["datasetStatus"] == FeedStatus.live.value
    assert data["publishedBy"] is None
    assert data["publishedAt"] == live_revision.published_at.isoformat()
    assert data["publishedAtDisplay"]
    assert data["severeErrors"] == []
    assert data["showPti"] is True
    assert data["hasPtiViolations"] is False
    assert data["distinctAttributes"] == {
        "PD0001": {"NOC1": {"42": ["PB0000001:1"], "7": ["PB0000001:1"]}}
    }
    assert data["dataQuality"] == {
        "reportId": None,
        "isNewService": False,
        "hasCriticalIssues": None,
        "rag": None,
    }


def test_feed_detail_reports_published_by_and_url_link(client, org_user, dataset):
    revision = dataset.live_revision
    revision.published_by = org_user
    revision.url_link = "https://example.com/feed.xml"
    revision.save()

    data = client.get(detail_url(dataset)).json()

    assert data["publishedBy"] == org_user.username
    assert data["urlLink"] == "https://example.com/feed.xml"


def test_feed_detail_hides_pti_for_revisions_before_pti_start(client, org_user):
    old = DatasetRevisionFactory(
        dataset__organisation=org_user.organisations.first(),
        dataset__dataset_type=TimetableType,
        created=datetime.datetime(2000, 1, 1),
    )

    data = client.get(detail_url(old.dataset)).json()

    assert data["showPti"] is False


def test_feed_detail_flags_pti_violations(client, dataset):
    PTIObservationFactory(revision=dataset.live_revision)

    data = client.get(detail_url(dataset)).json()

    assert data["hasPtiViolations"] is True


@pytest.mark.parametrize("flag_active", [False, True])
def test_feed_detail_legacy_data_quality_score(client, dataset, flag_active):
    report = DataQualityReportFactory(revision=dataset.live_revision, score=0.91)

    with override_flag(DQS_FLAG, active=flag_active):
        data = client.get(detail_url(dataset)).json()

    assert data["dataQuality"] == {
        "reportId": report.id,
        "isNewService": False,
        "hasCriticalIssues": None,
        "rag": {"score": "91%", "ragLevel": "amber", "cssIndicator": "warning"},
    }


@pytest.mark.parametrize("flag_active", [False, True])
def test_feed_detail_new_data_quality_service_without_critical_issues(
    client, dataset, flag_active
):
    report = ReportFactory(revision=dataset.live_revision)

    with override_flag(DQS_FLAG, active=flag_active):
        data = client.get(detail_url(dataset)).json()

    assert data["dataQuality"] == {
        "reportId": report.id,
        "isNewService": True,
        "hasCriticalIssues": False,
        "rag": None,
    }


def test_feed_detail_new_data_quality_service_with_critical_issues(client, dataset):
    report = ReportFactory(revision=dataset.live_revision)
    summary = mock.Mock(data={"Critical": {"count": 3}})

    with override_flag(DQS_FLAG, active=True), mock.patch(
        "transit_odp.publish.views.timetable.detail.Summary.get_report",
        return_value=summary,
    ):
        data = client.get(detail_url(dataset)).json()

    assert data["dataQuality"]["reportId"] == report.id
    assert data["dataQuality"]["hasCriticalIssues"] is True


def test_feed_detail_error_status_lists_severe_errors(client, dataset):
    DatasetETLErrorFactory(revision=dataset.live_revision, description="Bad file")

    data = client.get(detail_url(dataset)).json()

    assert data["status"] == "error"
    assert data["severeErrors"] == ["Bad file"]


def test_feed_detail_error_revision_status_without_error_rows(client, org_user):
    revision = DatasetRevisionFactory(
        dataset__organisation=org_user.organisations.first(),
        dataset__dataset_type=TimetableType,
        status=FeedStatus.error.value,
    )

    data = client.get(detail_url(revision.dataset)).json()

    assert data["status"] == "error"
    assert data["datasetStatus"] == FeedStatus.error.value
    assert data["severeErrors"] == []


def test_line_detail_uses_live_revision_and_forwards_query(client, dataset):
    build_line(dataset.live_revision)

    response = client.get(
        line_url(dataset),
        {"line": LINE_NAME, "service": SERVICE_CODE, "includeTimetable": "true"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["orgId"] == dataset.organisation_id
    assert data["datasetId"] == dataset.id
    assert data["revisionId"] == dataset.live_revision_id
    assert data["feedName"] == "Live timetable"
    assert data["lineName"] == LINE_NAME
    assert data["serviceCode"] == SERVICE_CODE
    assert data["serviceType"] == "Standard"
    assert [file["filename"] for file in data["currentValidFiles"]] == ["line-42.xml"]
    assert data["timetable"]["isTimetableInfoAvailable"] is True


def test_line_detail_omits_timetable_unless_requested(client, dataset):
    build_line(dataset.live_revision)

    data = client.get(
        line_url(dataset), {"line": LINE_NAME, "service": SERVICE_CODE}
    ).json()

    assert data["timetable"] is None
