from unittest.mock import Mock, patch

import pytest
from django.db.backends.base.base import BaseDatabaseWrapper
from django.http import HttpResponse
from django.test import Client, RequestFactory, override_settings

from transit_odp.common.middleware import HealthcheckMiddleware


@pytest.mark.parametrize("method", ["get", "head"])
@pytest.mark.parametrize(
    "path,host",
    [
        ("/healthcheck", "www.example.com"),
        ("/healthcheck", "10.0.0.1:8000"),
        ("/admin/healthcheck", "admin.example.com"),
        ("/admin/healthcheck", "10.0.0.1:8000"),
    ],
)
@override_settings(SECURE_SSL_REDIRECT=True)
def test_healthcheck_does_not_access_database(method, path, host):
    client = Client(HTTP_HOST=host)
    client.cookies["sessionid"] = "existing-session"

    with patch.object(
        BaseDatabaseWrapper,
        "ensure_connection",
        side_effect=AssertionError("Healthcheck attempted a database connection"),
    ):
        response = getattr(client, method)(f"{path}?probe=1")

    assert response.status_code == 200
    assert response.content == b""


@pytest.mark.parametrize(
    "path",
    ["/healthcheck/", "/admin/healthcheck/", "/admin/healthcheck-extra", "/other"],
)
def test_healthcheck_middleware_passes_other_paths_through(path):
    response = HttpResponse(status=204)
    get_response = Mock(return_value=response)
    request = RequestFactory().get(path)

    assert HealthcheckMiddleware(get_response)(request) is response
    get_response.assert_called_once_with(request)
