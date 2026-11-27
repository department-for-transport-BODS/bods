import datetime

import pytest
from django.utils import timezone
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.organisation.constants import (
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetMetadataFactory,
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
    OrganisationFactory,
)
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def make_dataset(status=FeedStatus.live.value, **kwargs):
    dataset = DatasetFactory(dataset_type=AVLType, **kwargs)
    revision = dataset.live_revision
    revision.status = status
    revision.save()
    return dataset


def detail_url(pk):
    return reverse("api:browser-avl-detail", host=DATA_HOST, kwargs={"pk": pk})


def get_detail(client_factory, pk, user=None):
    client = client_factory(host=DATA_HOST)
    if user is not None:
        client.force_login(user)
    return client.get(detail_url(pk))


def make_ppc_report(dataset, analysed, matching, granularity=PPCReportType.WEEKLY):
    return PostPublishingCheckReportFactory(
        dataset=dataset,
        granularity=granularity,
        vehicle_activities_analysed=analysed,
        vehicle_activities_completely_matching=matching,
    )


def test_url_is_served_on_the_data_host():
    assert detail_url(7).endswith("/api/browser/avl/7/")


def test_anonymous_user_gets_the_public_feed_detail(client_factory):
    dataset = make_dataset()
    revision = dataset.live_revision

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "id": dataset.id,
        "name": revision.name,
        "description": revision.description,
        "organisationId": dataset.organisation_id,
        "organisationName": dataset.organisation.name,
        "status": "live",
        "revisionId": revision.id,
        "lastUpdated": data["lastUpdated"],
        "lastAutomatedUpdate": None,
        "siriVmVersion": "",
        "avlTimetablesMatching": None,
        # The API URL and subscription state are for signed-in users only.
        "isSubscribed": False,
        "feedApi": None,
    }


def test_last_updated_matches_the_django_template_format(client_factory):
    dataset = make_dataset()

    data = get_detail(client_factory, dataset.id).json()

    # published_at|localtime|date:"j M Y H:i", in Europe/London.
    published = timezone.localtime(dataset.live_revision.published_at)
    assert data["lastUpdated"] == (
        f"{published.day} {published:%b %Y} {published:%H:%M}"
    )


def test_last_automated_update_is_formatted_in_local_time(client_factory):
    dataset = make_dataset()
    # 30 June 23:30 UTC is 1 July 00:30 in Europe/London (BST).
    checked = datetime.datetime(2026, 6, 30, 23, 30, tzinfo=datetime.timezone.utc)
    dataset.avl_feed_last_checked = checked
    dataset.save()

    data = get_detail(client_factory, dataset.id).json()

    assert data["lastAutomatedUpdate"] == "1 Jul 2026 00:30"


def test_siri_vm_version_comes_from_the_live_revision_metadata(client_factory):
    dataset = make_dataset()
    DatasetMetadataFactory(revision=dataset.live_revision, schema_version="2.0")

    data = get_detail(client_factory, dataset.id).json()

    assert data["siriVmVersion"] == "2.0"


def test_weekly_ppc_score_is_the_latest_weekly_report(client_factory):
    dataset = make_dataset()
    make_ppc_report(dataset, analysed=10, matching=5)
    make_ppc_report(dataset, analysed=3, matching=3, granularity=PPCReportType.DAILY)

    data = get_detail(client_factory, dataset.id).json()

    assert data["avlTimetablesMatching"] == "50%"


def test_matching_is_pending_when_the_report_analysed_nothing(client_factory):
    dataset = make_dataset()
    make_ppc_report(dataset, analysed=0, matching=0)

    data = get_detail(client_factory, dataset.id).json()

    assert data["avlTimetablesMatching"] is None


def test_signed_in_user_gets_api_url_and_subscription_state(client_factory):
    user = UserFactory()
    dataset = make_dataset()
    DatasetSubscriptionFactory(dataset=dataset, user=user)

    response = get_detail(client_factory, dataset.id, user=user)

    assert response.status_code == 200
    data = response.json()
    assert data["isSubscribed"] is True
    feed_path = reverse("api:avldetaildatafeedapi", args=[dataset.id], host=DATA_HOST)
    assert data["feedApi"] == f"{feed_path}?api_key={user.auth_token}"


def test_signed_in_user_who_is_not_subscribed(client_factory):
    user = UserFactory()
    dataset = make_dataset()

    data = get_detail(client_factory, dataset.id, user=user).json()

    assert data["isSubscribed"] is False
    assert data["feedApi"] is not None


@pytest.mark.parametrize(
    "status",
    [
        FeedStatus.live.value,
        FeedStatus.inactive.value,
        FeedStatus.expired.value,
        FeedStatus.error.value,
    ],
)
def test_any_published_status_is_viewable_like_django(client_factory, status):
    # Unlike timetables, Django's AVL detail view does not narrow by status.
    dataset = make_dataset(status=status)

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 200
    assert response.json()["status"] == status


def test_unpublished_feed_is_not_found(client_factory):
    revision = DatasetRevisionFactory(dataset__dataset_type=AVLType, is_published=False)

    response = get_detail(client_factory, revision.dataset_id)

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_feed_of_an_inactive_organisation_is_not_found(client_factory):
    dataset = make_dataset(organisation=OrganisationFactory(is_active=False))

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 404


@pytest.mark.parametrize("dataset_type", [TimetableType, FaresType])
def test_wrong_dataset_type_is_not_found(client_factory, dataset_type):
    dataset = DatasetFactory(dataset_type=dataset_type)

    response = get_detail(client_factory, dataset.id)

    assert response.status_code == 404


def test_unknown_feed_is_not_found(client_factory):
    assert get_detail(client_factory, 999999).status_code == 404


def test_only_get_is_allowed(client_factory):
    dataset = make_dataset()

    response = client_factory(host=DATA_HOST).post(detail_url(dataset.id))

    assert response.status_code == 405
