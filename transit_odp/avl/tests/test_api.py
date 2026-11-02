import datetime

import pytest
import pytz
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.factories import AVLDatasetRevisionFactory
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_feed_detail(client_factory, avl_feed_last_checked):
    user = UserFactory(account_type=OrgAdminType)
    revision = AVLDatasetRevisionFactory(
        dataset__organisation=user.organisations.first(),
    )
    dataset = revision.dataset
    dataset.avl_feed_last_checked = avl_feed_last_checked
    dataset.save()
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)
    url = reverse(
        "nextjs-avl-detail",
        host=PUBLISH_HOST,
        kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
    )
    response = client.get(url)
    assert response.status_code == 200
    return response.json()


def test_feed_detail_last_server_update_blank_when_never_checked(client_factory):
    detail = get_feed_detail(client_factory, avl_feed_last_checked=None)
    assert detail["lastServerUpdate"] == ""


def test_feed_detail_last_server_update_uses_last_checked(client_factory):
    detail = get_feed_detail(
        client_factory,
        avl_feed_last_checked=datetime.datetime(2026, 7, 15, 9, 35, tzinfo=pytz.utc),
    )
    assert detail["lastServerUpdate"] == "15 Jul 2026 10:35"
