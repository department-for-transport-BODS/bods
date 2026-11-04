import pytest
from django_hosts import reverse
from waffle.testutils import override_flag

from config.hosts import DATA_HOST
from transit_odp.browse.constants import LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.dqs.factories import ReportFactory
from transit_odp.organisation.constants import (
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def make_dataset(status=FeedStatus.live.value, with_etl_result=True, **kwargs):
    dataset = DatasetFactory(dataset_type=TimetableType, **kwargs)
    revision = dataset.live_revision
    revision.status = status
    revision.save()
    if with_etl_result:
        DatasetETLTaskResultFactory(revision=revision)
    return dataset


def detail_url(pk):
    return reverse("api:browser-timetable-detail", host=DATA_HOST, kwargs={"pk": pk})


def get_detail(client_factory, pk, user=None):
    client = client_factory(host=DATA_HOST)
    if user is not None:
        client.force_login(user)
    return client.get(detail_url(pk))


def test_url_is_served_on_the_data_host():
    assert detail_url(7).endswith("/api/browser/timetables/7/")


def test_anonymous_user_gets_the_public_dataset_detail(client_factory):
    dataset = make_dataset()
    revision = dataset.live_revision

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dataset.id
    assert data["name"] == revision.name
    assert data["description"] == revision.description
    assert data["organisationId"] == dataset.organisation_id
    assert data["organisationName"] == dataset.organisation.name
    assert data["status"] == "live"
    assert data["revisionId"] == revision.id
    assert data["transxchangeVersion"] == str(revision.transxchange_version)
    assert data["uploadFileExtension"] == "xml"
    assert data["error"] is False
    assert data["dataQuality"] is None
    assert data["serviceNumbers"] == []
    # The API URL and subscription state are for signed-in users only.
    assert data["feedApi"] is None
    assert data["isSubscribed"] is False


def test_last_updated_matches_the_django_template_format(client_factory):
    dataset = make_dataset()

    data = get_detail(client_factory, dataset.id).json()

    # published_at|date:"j M Y H:i", in the current (Europe/London) time zone.
    published = dataset.live_revision.published_at
    assert data["lastUpdated"].startswith(f"{published.day} {published:%b %Y} ")
    assert len(data["lastUpdated"].rsplit(" ", 1)[1]) == 5
    assert data["publishedBy"] is None


def test_published_by_username_is_returned(client_factory):
    publisher = UserFactory(username="publisher-user")
    dataset = make_dataset()
    revision = dataset.live_revision
    revision.published_by = publisher
    revision.save()

    data = get_detail(client_factory, dataset.id).json()

    assert data["publishedBy"] == "publisher-user"


def test_signed_in_user_gets_api_url_and_subscription_state(client_factory):
    user = UserFactory()
    dataset = make_dataset()
    DatasetSubscriptionFactory(dataset=dataset, user=user)

    response = get_detail(client_factory, dataset.id, user=user)

    assert response.status_code == 200
    data = response.json()
    assert data["isSubscribed"] is True
    feed_path = reverse("api:feed-detail", args=[dataset.id], host=DATA_HOST)
    assert data["feedApi"] == f"{feed_path}?api_key={user.auth_token}"


def test_signed_in_user_who_is_not_subscribed(client_factory):
    user = UserFactory()
    dataset = make_dataset()

    data = get_detail(client_factory, dataset.id, user=user).json()

    assert data["isSubscribed"] is False
    assert data["feedApi"] is not None


@pytest.mark.parametrize("status", [FeedStatus.live.value, FeedStatus.inactive.value])
def test_live_and_inactive_datasets_are_viewable(client_factory, status):
    dataset = make_dataset(status=status)

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 200
    assert response.json()["status"] == status


@pytest.mark.parametrize(
    "status",
    [
        FeedStatus.expired.value,
        FeedStatus.error.value,
        FeedStatus.pending.value,
        FeedStatus.indexing.value,
        FeedStatus.success.value,
    ],
)
def test_other_statuses_are_not_found(client_factory, status):
    dataset = make_dataset(status=status)

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_unpublished_dataset_is_not_found(client_factory):
    revision = DatasetRevisionFactory(
        dataset__dataset_type=TimetableType, is_published=False
    )

    response = get_detail(client_factory, revision.dataset_id)

    assert response.status_code == 404


def test_dataset_of_an_inactive_organisation_is_not_found(client_factory):
    dataset = make_dataset(organisation=OrganisationFactory(is_active=False))

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 404


@pytest.mark.parametrize("dataset_type", [AVLType, FaresType])
def test_wrong_dataset_type_is_not_found(client_factory, dataset_type):
    dataset = DatasetFactory(dataset_type=dataset_type)

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 404


def test_unknown_dataset_is_not_found(client_factory):
    assert get_detail(client_factory, 999999).status_code == 404


def test_only_get_is_allowed(client_factory):
    dataset = make_dataset()

    response = client_factory(host=DATA_HOST).post(detail_url(dataset.id))

    assert response.status_code == 405


def test_etl_error_is_reported(client_factory):
    dataset = make_dataset(with_etl_result=False)
    DatasetETLTaskResultFactory(
        revision=dataset.live_revision, error_code="SYSTEM_ERROR"
    )

    data = get_detail(client_factory, dataset.id).json()

    assert data["error"] is True


def test_service_numbers_are_grouped_by_licence_noc_and_line(client_factory):
    dataset = make_dataset()
    revision = dataset.live_revision
    TXCFileAttributesFactory(
        revision=revision,
        licence_number="PB0001",
        national_operator_code="NOC1",
        line_names=["10", "9"],
        service_code="SC2",
    )
    TXCFileAttributesFactory(
        revision=revision,
        licence_number="PB0001",
        national_operator_code="NOC1",
        line_names=["10"],
        service_code="SC1",
    )
    TXCFileAttributesFactory(
        revision=revision,
        licence_number="PB0002",
        national_operator_code="NOC2",
        line_names=["7"],
        service_code="SC3",
    )

    data = get_detail(client_factory, dataset.id).json()

    assert data["serviceNumbers"] == [
        {
            "licenceNumber": "PB0001",
            "nocs": [
                {
                    "noc": "NOC1",
                    "lines": [
                        {"lineName": "10", "serviceCodes": ["SC1", "SC2"]},
                        {"lineName": "9", "serviceCodes": ["SC2"]},
                    ],
                }
            ],
        },
        {
            "licenceNumber": "PB0002",
            "nocs": [
                {
                    "noc": "NOC2",
                    "lines": [{"lineName": "7", "serviceCodes": ["SC3"]}],
                }
            ],
        },
    ]


def test_blank_licence_number_uses_the_not_supplied_message(client_factory):
    dataset = make_dataset()
    TXCFileAttributesFactory(
        revision=dataset.live_revision, licence_number="  ", line_names=["1"]
    )

    data = get_detail(client_factory, dataset.id).json()

    assert (
        data["serviceNumbers"][0]["licenceNumber"]
        == LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
    )


def test_legacy_data_quality_score_is_returned(client_factory):
    dataset = make_dataset()
    DataQualityReportFactory(revision=dataset.live_revision, score=0.95)

    with override_flag("is_new_data_quality_service_active", active=False):
        data = get_detail(client_factory, dataset.id).json()

    quality = data["dataQuality"]
    assert quality["newDqsReport"] is False
    assert quality["score"] == "95%"
    assert quality["ragLevel"] == "AMBER"
    assert quality["cssIndicator"] == "warning"
    assert quality["reportId"] is not None


def test_no_data_quality_row_without_a_report(client_factory):
    dataset = make_dataset()

    with override_flag("is_new_data_quality_service_active", active=False):
        data = get_detail(client_factory, dataset.id).json()

    assert data["dataQuality"] is None


@pytest.mark.parametrize("flag_active", [True, False])
def test_new_data_quality_service_report(client_factory, flag_active):
    dataset = make_dataset()
    report = ReportFactory(revision=dataset.live_revision)

    with override_flag("is_new_data_quality_service_active", active=flag_active):
        with override_flag("is_specific_feedback", active=False):
            data = get_detail(client_factory, dataset.id).json()

    quality = data["dataQuality"]
    assert quality["newDqsReport"] is True
    assert quality["reportId"] == report.id
    assert quality["criticalCount"] == 0
    assert quality["feedbackCount"] is None
    assert quality["score"] is None


def test_new_data_quality_service_report_with_specific_feedback(client_factory):
    dataset = make_dataset()
    ReportFactory(revision=dataset.live_revision)

    with override_flag("is_new_data_quality_service_active", active=True):
        with override_flag("is_specific_feedback", active=True):
            data = get_detail(client_factory, dataset.id).json()

    quality = data["dataQuality"]
    assert quality["newDqsReport"] is True
    assert quality["criticalCount"] == 0
    assert quality["feedbackCount"] == 0
