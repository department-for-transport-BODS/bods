from unittest import mock

import pytest
from django.http import HttpResponse
from django.urls import clear_url_caches, path

from config import hosts
from transit_odp.common.utils.custom_error_handlers import server_error

pytestmark = pytest.mark.django_db


def broken_view(request):
    raise RuntimeError("boom")


@pytest.mark.parametrize(
    "host",
    [hosts.ROOT_HOST, hosts.DATA_HOST, hosts.PUBLISH_HOST, hosts.ADMIN_HOST],
)
def test_unhandled_error_renders_500_page(client_factory, settings, host):
    client = client_factory(host=host, raise_request_exception=False)
    urlconf = {
        hosts.ROOT_HOST: settings.ROOT_URLCONF,
        hosts.DATA_HOST: settings.DATA_URLCONF,
        hosts.PUBLISH_HOST: settings.PUBLISH_URLCONF,
        hosts.ADMIN_HOST: settings.ADMIN_URLCONF,
    }[host]
    module = __import__(urlconf, fromlist=["urlpatterns"])

    with mock.patch.object(
        module, "urlpatterns", [path("boom/", broken_view)] + module.urlpatterns
    ):
        clear_url_caches()
        response = client.get("/boom/")
    clear_url_caches()

    assert response.status_code == 500
    assert "Looks like something went wrong" in response.content.decode()


def test_server_error_falls_back_when_template_fails(rf):
    with mock.patch(
        "transit_odp.common.utils.custom_error_handlers.loader.get_template",
        side_effect=RuntimeError("template broke"),
    ):
        response = server_error(rf.get("/"))

    assert response.status_code == 500
    assert isinstance(response, HttpResponse)
