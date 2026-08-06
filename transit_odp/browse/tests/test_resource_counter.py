from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.avl.factories import CAVLDataArchiveFactory
from transit_odp.common.utils import reverse_path
from transit_odp.organisation.constants import FaresType
from transit_odp.pipelines.factories import BulkDataArchiveFactory
from transit_odp.site_admin.models import ResourceRequestCounter

pytestmark = pytest.mark.django_db(transaction=True)

SIGNED_URL = "https://example.test/signed-url"


def test_resource_counter_works_once(client_factory, user_factory):
    BulkDataArchiveFactory()
    consumer = user_factory()
    client = client_factory(host=DATA_HOST)
    client.force_login(consumer)
    url = reverse("downloads-bulk", host=DATA_HOST)

    with patch(
        "transit_odp.browse.views.timetable_views.generate_signed_url",
        return_value=SIGNED_URL,
    ):
        response = client.get(url)

    assert response.status_code == 302
    assert response["Location"] == SIGNED_URL

    resource_counter = ResourceRequestCounter.objects.first()
    assert resource_counter.requestor == consumer
    assert resource_counter.counter == 1


def test_resource_counter_works_twice(client_factory, user_factory):
    BulkDataArchiveFactory()
    consumer = user_factory()
    client = client_factory(host=DATA_HOST)
    client.force_login(consumer)
    url = reverse("downloads-bulk", host=DATA_HOST)

    with patch(
        "transit_odp.browse.views.timetable_views.generate_signed_url",
        return_value=SIGNED_URL,
    ):
        client.get(url)
        client.get(url)

    resource_counter = ResourceRequestCounter.objects.first()
    assert resource_counter.requestor == consumer
    assert resource_counter.counter == 2


def test_resource_counter_user_not_logged(client_factory):
    BulkDataArchiveFactory()
    client = client_factory(host=DATA_HOST)
    AnonymousUser()
    url = reverse("downloads-bulk", host=DATA_HOST)

    with patch(
        "transit_odp.browse.views.timetable_views.generate_signed_url",
        return_value=SIGNED_URL,
    ):
        response = client.get(url)

    resource_counter = ResourceRequestCounter.objects.first()
    assert response.status_code == 302
    assert resource_counter.requestor is None
    assert resource_counter.counter == 1


def test_multiple_resource_counters(client_factory, user_factory):
    """
    Progressively hit multiple resource counter endpoints
    checking each time
    """
    BulkDataArchiveFactory()
    BulkDataArchiveFactory(dataset_type=FaresType)
    CAVLDataArchiveFactory()
    consumer = user_factory()
    client = client_factory(host=DATA_HOST)
    client.force_login(consumer)

    with patch(
        "transit_odp.browse.views.timetable_views.generate_signed_url",
        return_value=SIGNED_URL,
    ), patch(
        "transit_odp.browse.views.avl_views.generate_signed_url",
        return_value=SIGNED_URL,
    ), patch(
        "transit_odp.browse.views.fares_views.generate_signed_url",
        return_value=SIGNED_URL,
    ):
        for view in ("downloads-bulk", "downloads-avl-bulk", "downloads-fares-bulk"):
            url = reverse(view, host=DATA_HOST)
            for counter in range(3):
                expected = counter + 1
                client.get(url)
                resource_counter = ResourceRequestCounter.objects.get(
                    path_info=reverse_path(view, host=DATA_HOST)
                )
                assert resource_counter.counter == expected
