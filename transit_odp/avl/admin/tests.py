import pytest
from django.utils import timezone
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import DATA_HOST, PUBLISH_HOST
from transit_odp.avl.proxies import AVLDataset
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.organisation.models import DatasetRevision
from transit_odp.users.factories import OrgAdminFactory

from ...users.constants import DeveloperType
from .forms import create_dummy_avl_datafeed

pytestmark = pytest.mark.django_db

url = "http://test.com"
password = "password"
username = "username"
description = "description"
short_description = "sd"
now = timezone.now()


@freeze_time(now)
def test_successfully_creates_dummy_dataset():
    organisation = OrganisationFactory()
    contact = OrgAdminFactory(organisations=(organisation,))
    organisation.key_contact = contact
    organisation.save()

    dataset = AVLDataset()
    create_dummy_avl_datafeed(
        dataset, url, username, password, organisation, description, short_description
    )
    fetched_dataset = AVLDataset.objects.first()

    assert fetched_dataset.organisation == organisation
    assert fetched_dataset.is_dummy
    assert fetched_dataset.live_revision.url_link == url
    assert fetched_dataset.live_revision.password == password
    assert fetched_dataset.live_revision.username == username
    assert fetched_dataset.live_revision.description == description
    assert fetched_dataset.live_revision.short_description == short_description
    assert fetched_dataset.contact == contact
    assert fetched_dataset.live_revision.is_published
    assert fetched_dataset.live_revision.published_at == now
    assert fetched_dataset.live_revision.published_by == contact
    assert fetched_dataset.live_revision.comment == "First publication"


def test_successfully_creates_two_dummy_dataset():
    organisation = OrganisationFactory()
    contact = OrgAdminFactory(organisations=(organisation,))
    organisation.key_contact = contact
    organisation.save()

    dataset = AVLDataset()
    create_dummy_avl_datafeed(
        dataset, url, username, password, organisation, description, short_description
    )

    dataset = AVLDataset()
    create_dummy_avl_datafeed(
        dataset, url, username, password, organisation, description, short_description
    )

    assert AVLDataset.objects.count() == 2
    assert DatasetRevision.objects.count() == 2


def test_can_edit_dataset():
    organisation = OrganisationFactory()
    contact = OrgAdminFactory(organisations=(organisation,))
    organisation.key_contact = contact
    organisation.save()

    dataset = AVLDataset()
    create_dummy_avl_datafeed(
        dataset, url, username, password, organisation, description, short_description
    )
    create_dummy_avl_datafeed(
        dataset, url, "changed", password, organisation, description, short_description
    )

    fetched_dataset = AVLDataset.objects.first()

    assert AVLDataset.objects.count() == 1
    assert DatasetRevision.objects.count() == 1
    assert fetched_dataset.live_revision.username == "changed"


@pytest.mark.parametrize(
    "url_name",
    ["avl:feed-archive", "avl:feed-update", "avl:dataset-edit"],
    ids=(
        "publisher cannot archive dummy dataset",
        "publisher cannot update dummy dataset",
        "publisher cannot description edit dummy dataset",
    ),
)
def test_org_publisher_cannot_change_dummy_datasets(client_factory, url_name):
    organisation = OrganisationFactory()
    contact = OrgAdminFactory(organisations=(organisation,))
    organisation.key_contact = contact
    organisation.save()

    dataset = AVLDataset()
    create_dummy_avl_datafeed(
        dataset, url, username, password, organisation, description, short_description
    )

    archive_url = reverse(
        url_name,
        kwargs={"pk1": organisation.id, "pk": dataset.id},
        host=PUBLISH_HOST,
    )
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user=contact)

    response = client.get(archive_url)
    assert response.status_code == 404


def test_dummy_dataset_is_visible_to_consumer(client_factory, user_factory):
    organisation = OrganisationFactory()
    contact = OrgAdminFactory(organisations=(organisation,))
    organisation.key_contact = contact
    organisation.save()

    dataset = AVLDataset()
    create_dummy_avl_datafeed(
        dataset, url, username, password, organisation, description, short_description
    )

    developer = user_factory(account_type=DeveloperType)
    search_url = reverse("avl-search", host=DATA_HOST)
    client = client_factory(host=DATA_HOST)
    client.force_login(user=developer)

    response = client.get(search_url)
    assert response.context_data["object_list"].count() == 1


def test_dummy_dataset_is_visible_to_publisher(client_factory):
    organisation = OrganisationFactory()
    contact = OrgAdminFactory(organisations=(organisation,))
    organisation.key_contact = contact
    organisation.save()

    dataset = AVLDataset()
    create_dummy_avl_datafeed(
        dataset, url, username, password, organisation, description, short_description
    )

    search_url = reverse(
        "avl:feed-list", kwargs={"pk1": organisation.id}, host=PUBLISH_HOST
    )
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user=contact)

    response = client.get(search_url)
    assert response.context_data["active_feeds"].count() == 1
