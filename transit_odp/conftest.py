from datetime import timedelta

import pytest
from django.conf import settings
from django.test import RequestFactory
from django.test.client import Client
from django.utils.timezone import localtime
from django_hosts import reverse_host
from pytest_django.lazy_django import skip_if_no_django
from pytest_factoryboy import register

from config import hosts
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.transmodel.factories import StopActivityFactory
from transit_odp.transmodel.models import StopActivity
from transit_odp.users.factories import InvitationFactory, UserFactory

# TODO - remove these as they make refactoring awkward
register(UserFactory)
register(InvitationFactory)
register(OrganisationFactory)


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture()
def client_factory():
    """Client factory to ease testing multi-host site"""

    def _inner(host: str, *args, **kwargs):
        skip_if_no_django()
        hostname = reverse_host(host)
        return Client(HTTP_HOST=hostname, *args, **kwargs)

    return _inner


@pytest.fixture()
def root_client(client_factory):
    return client_factory(host=hosts.ROOT_HOST)


@pytest.fixture()
def data_client(client_factory):
    return client_factory(host=hosts.DATA_HOST)


@pytest.fixture()
def publish_client(client_factory):
    return client_factory(host=hosts.PUBLISH_HOST)


@pytest.fixture()
def admin_client(client_factory):
    return client_factory(host=hosts.ADMIN_HOST)


@pytest.fixture()
def bods_mailoutbox(settings, mailoutbox):
    """Hack to make tests fail when templates have undefined variables. This
    is particularly useful as it is the same behaviour as gov-notify"""

    class InvalidString:
        def __contains__(self, key):
            return key == "%s"

        def __mod__(self, other):
            pytest.fail(f"undefined variable {other}")

    settings.TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = InvalidString()
    yield mailoutbox
    del settings.TEMPLATES[0]["OPTIONS"]["string_if_invalid"]


@pytest.fixture
def pti_enforced():
    original_value = settings.PTI_ENFORCED_DATE
    the_past = localtime() - timedelta(days=7)
    the_past = the_past.replace(hour=0, minute=0, second=0, microsecond=0)
    settings.PTI_ENFORCED_DATE = the_past
    yield settings.PTI_ENFORCED_DATE
    settings.PTI_ENFORCED_DATE = original_value


@pytest.fixture
def pti_unenforced():
    original_value = settings.PTI_ENFORCED_DATE
    the_future = localtime() + timedelta(days=7)
    the_future = the_future.replace(hour=0, minute=0, second=0, microsecond=0)
    settings.PTI_ENFORCED_DATE = the_future
    yield settings.PTI_ENFORCED_DATE
    settings.PTI_ENFORCED_DATE = original_value


@pytest.fixture(scope="session", autouse=True)
def setup_stop_activities(django_db_setup, django_db_blocker):
    stop_activities = [
        "none",
        "pickUp",
        "setDown",
        "pickUpAndSetDown",
        "pass",
        "pickUpDriverRequest",
        "setDownDriverRequest",
        "pickUpAndSetDownDriverRequest",
    ]

    with django_db_blocker.unblock():
        # Clear existing StopActivity records
        StopActivity.objects.all().delete()
        for index, stop in enumerate(stop_activities):
            StopActivityFactory(name=stop, id=index + 1)
