import json

import pytest

from config import hosts
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.users.constants import DATASET_MANAGE_TABLE_PAGINATE_BY
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

SUBSCRIPTIONS_URL = "/api/auth/subscriptions/"
MUTE_URL = "/api/auth/subscriptions/mute/"


def test_subscriptions_requires_authentication(client_factory):
    client = client_factory(host=hosts.DATA_HOST)

    response = client.get(SUBSCRIPTIONS_URL)

    assert response.status_code == 401


def test_subscriptions_empty_list(user, client_factory):
    client = client_factory(host=hosts.DATA_HOST)
    client.force_login(user=user)

    response = client.get(SUBSCRIPTIONS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0
    assert payload["results"] == []
    assert payload["muteNotifications"] is False
    assert payload["pageSize"] == DATASET_MANAGE_TABLE_PAGINATE_BY


def test_subscriptions_lists_only_the_signed_in_users_datasets(user, client_factory):
    client = client_factory(host=hosts.DATA_HOST)
    client.force_login(user=user)
    other = UserFactory()

    subscribed = DatasetRevisionFactory()
    subscribed.dataset.subscribers.add(user)
    ignored = DatasetRevisionFactory()
    ignored.dataset.subscribers.add(other)

    response = client.get(SUBSCRIPTIONS_URL)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["id"] == subscribed.dataset_id
    assert payload["results"][0]["name"] == subscribed.name
    assert payload["results"][0]["datasetType"] == "TIMETABLE"
    assert payload["results"][0]["statusLabel"] == "Published"


def test_subscriptions_paginates(user, client_factory):
    client = client_factory(host=hosts.DATA_HOST)
    client.force_login(user=user)

    for revision in DatasetRevisionFactory.create_batch(11):
        revision.dataset.subscribers.add(user)

    first_page = client.get(SUBSCRIPTIONS_URL).json()
    second_page = client.get(SUBSCRIPTIONS_URL, data={"page": 2}).json()

    assert first_page["count"] == 11
    assert first_page["totalPages"] == 2
    assert len(first_page["results"]) == 10
    assert len(second_page["results"]) == 1
    assert second_page["page"] == 2


def test_mute_subscriptions(user, client_factory):
    client = client_factory(host=hosts.DATA_HOST)
    client.force_login(user=user)

    response = client.post(
        MUTE_URL,
        data=json.dumps({"muteNotifications": True}),
        content_type="application/json",
    )

    user.refresh_from_db()

    assert response.status_code == 200
    assert response.json()["muteNotifications"] is True
    assert user.settings.mute_all_dataset_notifications is True
