import json

import pytest
from django_hosts import reverse
from waffle.testutils import override_flag

from config.hosts import PUBLISH_HOST
from transit_odp.dqs.constants import Checks, Level
from transit_odp.dqs.factories import (
    ChecksFactory,
    ObservationResultsFactory,
    ReportFactory,
    TaskResultsFactory,
)
from transit_odp.dqs.models import ObservationResults
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import (
    ConsumerFeedbackFactory,
    DatasetRevisionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import ConsumerFeedback
from transit_odp.transmodel.factories import ServiceFactory, ServicePatternFactory
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

SERVICE_CODE = "PB0000001:1"
LINE_NAME = "42"


@pytest.fixture
def dq_report(client_factory):
    user = UserFactory(account_type=OrgAdminType)
    revision = DatasetRevisionFactory(
        dataset__organisation=user.organisations.first(),
        dataset__dataset_type=TimetableType,
        is_published=False,
    )
    report = ReportFactory(revision=revision)
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)
    return client, user, revision, report


def _url(report, name, slug=None):
    kwargs = {
        "pk1": report.revision.dataset.organisation_id,
        "pk": report.revision.dataset_id,
        "report_id": report.id,
    }
    if slug is not None:
        kwargs["slug"] = slug
    return reverse(name, host=PUBLISH_HOST, kwargs=kwargs)


def _list_url(report, slug):
    return _url(report, "nextjs-timetables-data-quality-observation", slug)


def _detail_url(report, slug):
    return _url(report, "nextjs-timetables-data-quality-observation-detail", slug)


def _suppress_url(report, slug):
    return _url(report, "nextjs-timetables-data-quality-observation-suppress", slug)


def _create_observation(report, check, level, service_code=SERVICE_CODE, **kwargs):
    txc = TXCFileAttributesFactory(revision=report.revision, service_code=service_code)
    ServiceFactory(
        revision=report.revision,
        txcfileattributes=txc,
        service_code=service_code,
        name=LINE_NAME,
    )
    task = TaskResultsFactory(
        dataquality_report=report,
        transmodel_txcfileattributes=txc,
        checks=ChecksFactory(observation=check.value, importance=level.value),
    )
    kwargs.setdefault("is_suppressed", False)
    return ObservationResultsFactory(taskresults=task, **kwargs)


def test_observation_list_returns_definition_and_rows(dq_report):
    client, _, revision, report = dq_report
    _create_observation(report, Checks.IncorrectStopType, Level.critical)

    response = client.get(_list_url(report, "incorrect-stop-type"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["reportId"] == report.id
    assert payload["revisionId"] == revision.id
    assert payload["isPublished"] is False
    assert payload["hasDetail"] is True
    assert payload["canSuppress"] is False
    assert payload["observation"]["title"] == "Incorrect stop type"
    assert payload["observation"]["level"] == "Critical"
    assert payload["observation"]["extraInfo"]
    assert payload["totalCount"] == 1
    assert payload["rows"] == [
        {
            "serviceCode": SERVICE_CODE,
            "lineName": LINE_NAME,
            "details": "There is at least one stop with an incorrect stop type",
            "isSuppressed": False,
        }
    ]


def test_observation_list_uses_column_details_without_detail_link(dq_report):
    client, _, _, report = dq_report
    _create_observation(report, Checks.IncorrectNoc, Level.critical)

    payload = client.get(_list_url(report, "incorrect-noc")).json()

    assert payload["hasDetail"] is False
    assert payload["canSuppress"] is False
    assert payload["rows"][0]["details"].endswith(
        " is specified in the dataset but not assigned to your organisation"
    )


def test_observation_list_paginates(dq_report):
    client, _, _, report = dq_report
    for index in range(11):
        _create_observation(
            report, Checks.MissingJourneyCode, Level.advisory, f"PB{index:07d}:1"
        )

    url = _list_url(report, "missing-journey-code")
    first = client.get(url).json()
    second = client.get(url, {"page": 2}).json()

    assert (first["totalCount"], first["totalPages"], len(first["rows"])) == (
        11,
        2,
        10,
    )
    assert (second["page"], len(second["rows"])) == (2, 1)


def test_observation_list_unknown_slug_returns_404(dq_report):
    client, _, _, report = dq_report

    assert client.get(_list_url(report, "missing-stops")).status_code == 404


def test_observation_endpoints_require_org_membership(dq_report, client_factory):
    _, _, _, report = dq_report
    client = client_factory(host=PUBLISH_HOST)
    url = _list_url(report, "incorrect-stop-type")

    assert client.get(url).status_code == 401
    client.force_login(UserFactory(account_type=OrgAdminType))
    assert client.get(url).status_code in (403, 404)


def test_observation_endpoints_reject_report_from_other_dataset(dq_report):
    client, user, _, report = dq_report
    other_revision = DatasetRevisionFactory(
        dataset__organisation=user.organisations.first(),
        dataset__dataset_type=TimetableType,
    )
    other_report = ReportFactory(revision=other_revision)
    url = reverse(
        "nextjs-timetables-data-quality-observation",
        host=PUBLISH_HOST,
        kwargs={
            "pk1": report.revision.dataset.organisation_id,
            "pk": report.revision.dataset_id,
            "report_id": other_report.id,
            "slug": "incorrect-stop-type",
        },
    )

    assert client.get(url).status_code == 404


def test_observation_detail_returns_configured_columns(dq_report):
    client, _, _, report = dq_report
    _create_observation(report, Checks.DuplicateJourneyCode, Level.advisory)

    response = client.get(
        _detail_url(report, "duplicate-journey-code"),
        {"service": SERVICE_CODE, "line": LINE_NAME},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Duplicate journey code"
    assert payload["subtitle"] == (
        f"Service {LINE_NAME} has at least one journey with a duplicate journey code"
    )
    assert payload["subtitleDescription"] == "Which journeys have been affected?"
    assert payload["totalCount"] == 1
    assert payload["isFeedback"] is False
    assert [column["label"] for column in payload["columns"]] == [
        "Journey start time",
        "Direction",
        "First stop",
        "Journey code",
    ]
    assert set(payload["rows"][0]["values"]) == {
        "journey_start_time",
        "direction",
        "stop_name",
        "journey_code",
    }


def test_observation_detail_requires_service_and_line(dq_report):
    client, _, _, report = dq_report

    response = client.get(_detail_url(report, "duplicate-journey-code"))

    assert response.status_code == 400


def test_observation_detail_not_available_for_list_only_observation(dq_report):
    client, _, _, report = dq_report

    response = client.get(
        _detail_url(report, "incorrect-noc"),
        {"service": SERVICE_CODE, "line": LINE_NAME},
    )

    assert response.status_code == 404


def test_suppress_advisory_observation_for_service(dq_report):
    client, _, _, report = dq_report
    observation = _create_observation(
        report, Checks.StopNotFoundInNaptan, Level.advisory
    )
    other = _create_observation(
        report, Checks.StopNotFoundInNaptan, Level.advisory, "PB0000002:1"
    )

    response = client.post(
        _suppress_url(report, "stop-not-in-naptan"),
        data=json.dumps(
            {"serviceCode": SERVICE_CODE, "lineName": LINE_NAME, "isSuppressed": True}
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {"updated": 1, "isSuppressed": True}
    assert ObservationResults.objects.get(id=observation.id).is_suppressed is True
    assert ObservationResults.objects.get(id=other.id).is_suppressed is False


def test_suppress_all_advisory_observations(dq_report):
    client, _, _, report = dq_report
    for code in (SERVICE_CODE, "PB0000002:1"):
        _create_observation(report, Checks.StopNotFoundInNaptan, Level.advisory, code)

    response = client.post(
        _suppress_url(report, "stop-not-in-naptan"),
        data=json.dumps({"isSuppressed": True}),
        content_type="application/json",
    )

    assert response.json()["updated"] == 2
    assert not ObservationResults.objects.filter(is_suppressed=False).exists()


def test_suppress_rejects_critical_observation(dq_report):
    client, _, _, report = dq_report

    response = client.post(
        _suppress_url(report, "incorrect-noc"),
        data=json.dumps({"isSuppressed": True}),
        content_type="application/json",
    )

    assert response.status_code == 400


def test_suppress_feedback_row_for_draft_revision(dq_report):
    client, user, revision, report = dq_report
    service = ServiceFactory(revision=revision, service_code=SERVICE_CODE)
    pattern = ServicePatternFactory(revision=revision, line_name=LINE_NAME)
    service.service_patterns.add(pattern)
    feedbacks = [
        ConsumerFeedbackFactory(
            revision=revision,
            dataset=revision.dataset,
            organisation=user.organisations.first(),
            service=service,
            service_pattern=pattern,
            is_suppressed=False,
        )
        for _ in range(2)
    ]

    response = client.post(
        _suppress_url(report, "feedback"),
        data=json.dumps(
            {
                "serviceCode": SERVICE_CODE,
                "lineName": LINE_NAME,
                "rowId": feedbacks[0].id,
                "isSuppressed": True,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["updated"] == 1
    assert ConsumerFeedback.objects.get(id=feedbacks[0].id).is_suppressed is True
    assert ConsumerFeedback.objects.get(id=feedbacks[1].id).is_suppressed is False


@pytest.mark.parametrize(
    "feedback_flag, expected_levels",
    [
        (False, ["Critical", "Advisory"]),
        (True, ["Critical", "Advisory", "Feedback"]),
    ],
)
def test_data_quality_definitions_are_public(
    client_factory, feedback_flag, expected_levels
):
    client = client_factory(host=PUBLISH_HOST)
    url = reverse("nextjs-data-quality-definitions", host=PUBLISH_HOST)

    with override_flag("is_specific_feedback", active=feedback_flag):
        response = client.get(url)

    assert response.status_code == 200
    levels = response.json()["levels"]
    assert [level["level"] for level in levels] == expected_levels
    critical = levels[0]
    assert critical["count"] == sum(
        len(category["observations"]) for category in critical["categories"]
    )
    assert all(category["showCategory"] for category in critical["categories"])
    observation = critical["categories"][0]["observations"][0]
    assert {"title", "text", "impacts", "isActive", "extraInfo"} <= set(observation)
