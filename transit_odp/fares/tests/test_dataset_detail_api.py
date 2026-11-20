import datetime

import pytest
from django.utils import timezone
from django_hosts import reverse
from waffle.testutils import override_flag

from config.hosts import DATA_HOST
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.fares_validator.factories import FaresValidationResultFactory
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
)
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def make_dataset(status=FeedStatus.live.value, with_metadata=True, **kwargs):
    dataset = DatasetFactory(dataset_type=FaresType, **kwargs)
    revision = dataset.live_revision
    revision.status = status
    revision.save()
    if with_metadata:
        FaresMetadataFactory(
            revision=revision,
            schema_version="1.1",
            num_of_fare_zones=4,
            num_of_lines=5,
            num_of_sales_offer_packages=6,
            num_of_fare_products=7,
            num_of_user_profiles=8,
            valid_from=datetime.datetime(
                2026, 7, 1, 9, 30, tzinfo=datetime.timezone.utc
            ),
            valid_to=None,
        )
    return dataset


def detail_url(pk):
    return reverse("api:browser-fares-detail", host=DATA_HOST, kwargs={"pk": pk})


def get_detail(client_factory, pk, user=None):
    client = client_factory(host=DATA_HOST)
    if user is not None:
        client.force_login(user)
    return client.get(detail_url(pk))


def test_url_is_served_on_the_data_host():
    assert detail_url(7).endswith("/api/browser/fares/7/")


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
    assert data["uploadFileExtension"] == "xml"
    assert data["publishedBy"] is None
    assert data["showMap"] is True
    # The API URL and subscription state are for signed-in users only.
    assert data["feedApi"] is None
    assert data["isSubscribed"] is False


def test_last_updated_matches_the_django_template_format(client_factory):
    dataset = make_dataset()

    data = get_detail(client_factory, dataset.id).json()

    # published_at|localtime|date:"j M Y H:i", in Europe/London.
    published = timezone.localtime(dataset.live_revision.published_at)
    assert data["lastUpdated"] == (
        f"{published.day} {published:%b %Y} {published:%H:%M}"
    )


def test_metadata_is_rendered_the_way_the_template_prints_it(client_factory):
    dataset = make_dataset()

    metadata = get_detail(client_factory, dataset.id).json()["metadata"]

    assert metadata == {
        "schemaVersion": "1.1",
        "numOfFareZones": "4",
        "numOfLines": "5",
        "numOfSalesOfferPackages": "6",
        "numOfFareProducts": "7",
        "numOfUserProfiles": "8",
        # {{ valid_from }}: localised datetime in Europe/London (BST = UTC+1).
        "validFrom": "July 1, 2026, 10:30 a.m.",
        # {{ None }} prints "None" in a Django template.
        "validTo": "None",
    }


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
    feed_path = reverse("api:fares-api-detail", args=[dataset.id], host=DATA_HOST)
    assert data["feedApi"] == f"{feed_path}?api_key={user.auth_token}"


def test_signed_in_user_who_is_not_subscribed(client_factory):
    user = UserFactory()
    dataset = make_dataset()

    data = get_detail(client_factory, dataset.id, user=user).json()

    assert data["isSubscribed"] is False
    assert data["feedApi"] is not None


def test_dataset_without_a_validation_result_is_non_compliant_without_report(
    client_factory,
):
    dataset = make_dataset()

    data = get_detail(client_factory, dataset.id).json()

    assert data["isCompliantError"] is True
    assert data["showReportLink"] is False


@pytest.mark.parametrize(
    ("violations", "expected_compliant_error"), [(0, False), (3, True)]
)
def test_validation_result_drives_the_compliance_row(
    client_factory, violations, expected_compliant_error
):
    dataset = make_dataset()
    FaresValidationResultFactory(
        revision=dataset.live_revision,
        organisation=dataset.organisation,
        count=violations,
    )

    data = get_detail(client_factory, dataset.id).json()

    assert data["isCompliantError"] is expected_compliant_error
    assert data["showReportLink"] is True


@pytest.mark.parametrize("flag_active", [True, False])
def test_payload_carries_the_facts_for_both_fares_validator_flag_states(
    client_factory, flag_active
):
    # The flag only decides whether Next.js renders the compliance row; the
    # facts it branches on are always returned.
    dataset = make_dataset()
    FaresValidationResultFactory(
        revision=dataset.live_revision,
        organisation=dataset.organisation,
        count=3,
    )

    with override_flag("is_fares_validator_active", active=flag_active):
        response = get_detail(client_factory, dataset.id)

    assert response.status_code == 200
    data = response.json()
    assert data["isCompliantError"] is True
    assert data["showReportLink"] is True


@pytest.mark.parametrize(
    ("status", "show_map"),
    [
        (FeedStatus.live.value, True),
        (FeedStatus.inactive.value, True),
        (FeedStatus.expired.value, True),
        (FeedStatus.expiring.value, False),
        (FeedStatus.warning.value, False),
        (FeedStatus.error.value, False),
    ],
)
def test_status_decides_whether_the_map_is_shown(client_factory, status, show_map):
    dataset = make_dataset(status=status)

    data = get_detail(client_factory, dataset.id).json()

    assert data["status"] == status
    assert data["showMap"] is show_map


def test_unpublished_dataset_is_not_found(client_factory):
    revision = DatasetRevisionFactory(
        dataset__dataset_type=FaresType, is_published=False
    )

    response = get_detail(client_factory, revision.dataset_id)

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_dataset_of_an_inactive_organisation_is_not_found(client_factory):
    dataset = make_dataset(organisation=OrganisationFactory(is_active=False))

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 404


@pytest.mark.parametrize("dataset_type", [TimetableType, AVLType])
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
