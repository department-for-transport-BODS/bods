import pytest
from django.test import RequestFactory
from django.test.client import Client
from django_hosts import reverse_host
from pytest_django.lazy_django import skip_if_no_django
from pytest_factoryboy import register

from config import hosts
from transit_odp.organisation.factories import OrganisationFactory
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
