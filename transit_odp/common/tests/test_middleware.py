from random import choices
from string import ascii_letters
from unittest.mock import patch

import pytest
from django.db import DatabaseError, connection
from django_hosts.resolvers import reverse

import config
from transit_odp.site_admin.models import CHAR_LEN, APIRequest
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_api_request_middleware(client_factory):
    host = config.hosts.DATA_HOST
    url = reverse("api:fares-api-list", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)

    assert APIRequest.objects.count() == 0
    client.get(url, {"noc": "BLAH", "status": "active"})
    assert APIRequest.objects.count() == 1
    request = APIRequest.objects.first()
    assert request.requestor == user
    assert request.path_info == "/api/v1/fares/dataset/"
    assert request.query_string == "noc=BLAH&status=active"


def test_api_request_middleware_long_query_params(client_factory):
    """Test what happens if query parameter string len > CHAR_LEN"""
    host = config.hosts.DATA_HOST
    url = reverse("api:fares-api-list", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)
    noc = "".join(choices(ascii_letters, k=CHAR_LEN + 1))

    assert APIRequest.objects.count() == 0
    client.get(url, {"noc": noc})
    assert APIRequest.objects.count() == 1
    request = APIRequest.objects.first()
    assert request.requestor == user
    assert request.path_info == "/api/v1/fares/dataset/"
    expected = "noc=" + noc
    assert request.query_string == expected[:CHAR_LEN]


def test_api_request_middleware_unauthorized(client_factory):
    host = config.hosts.DATA_HOST
    url = reverse("api:fares-api-list", host=host)
    client = client_factory(host=host)
    UserFactory()
    assert APIRequest.objects.count() == 0
    response = client.get(url, {"noc": "BLAH", "status": "active"})
    assert response.status_code == 401
    assert APIRequest.objects.count() == 0


def test_api_request_middleware_swagger_page(client_factory):
    host = config.hosts.DATA_HOST
    # not api endpoint just the swagger page
    url = reverse("api:faresopenapi", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)

    assert APIRequest.objects.count() == 0
    client.get(url, {"noc": "BLAH", "status": "active"})
    assert APIRequest.objects.count() == 0


def test_api_request_middleware_home_page_logged_in(client_factory):
    host = config.hosts.DATA_HOST
    # not api endpoint just the swagger page
    url = reverse("home", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)

    assert APIRequest.objects.count() == 0
    client.get(url, {"noc": "BLAH", "status": "active"})
    assert APIRequest.objects.count() == 0


def test_api_request_middleware_remove_api_key(client_factory):
    host = config.hosts.DATA_HOST
    url = reverse("api:fares-api-list", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)

    assert APIRequest.objects.count() == 0
    client.get(url, {"noc": "BLAH", "api_key": user.auth_token.key, "status": "active"})
    assert APIRequest.objects.count() == 1
    request = APIRequest.objects.first()
    assert request.requestor == user
    assert request.path_info == "/api/v1/fares/dataset/"
    assert request.query_string == "noc=BLAH&status=active"


@pytest.fixture
def exhausted_api_request_id_sequence():
    """Next APIRequest insert succeeds, the one after hits the sequence ceiling.

    ALTER SEQUENCE is transactional, so the test's rollback restores it.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_get_serial_sequence('site_admin_apirequest', 'id')")
        (sequence,) = cursor.fetchone()
        cursor.execute(f"ALTER SEQUENCE {sequence} MAXVALUE 5 RESTART WITH 5")


def test_api_request_middleware_survives_id_sequence_exhaustion(
    client_factory, exhausted_api_request_id_sequence, caplog
):
    host = config.hosts.DATA_HOST
    url = reverse("api:fares-api-list", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)

    first = client.get(url, {"noc": "BLAH"})
    second = client.get(url, {"noc": "BLAH"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert list(APIRequest.objects.values_list("id", flat=True)) == [5]
    assert "Failed to log API request" in caplog.text
    assert "reached maximum value of sequence" in caplog.text


def test_api_request_middleware_survives_database_error(client_factory, caplog):
    host = config.hosts.DATA_HOST
    url = reverse("api:fares-api-list", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)

    with patch.object(
        APIRequest.objects, "create", side_effect=DatabaseError("db unavailable")
    ):
        response = client.get(url, {"noc": "BLAH"})

    assert response.status_code == 200
    assert APIRequest.objects.count() == 0
    assert "Failed to log API request" in caplog.text
    assert "db unavailable" in caplog.text


def test_security_headers(client_factory):
    host = config.hosts.DATA_HOST
    url = reverse("home", host=host)
    client = client_factory(host=host)
    user = UserFactory()
    client.force_login(user=user)
    response = client.get(
        url, {"noc": "BLAH", "api_key": user.auth_token.key, "status": "active"}
    )
    # Check the Permissions-Policy header
    assert (
        response["Permissions-Policy"]
        == "geolocation=(self), microphone=(self), camera=(self)"
    )
    # Extract the Content-Security-Policy header
    csp_header = response["Content-Security-Policy"]
    expected_directives = [
        "default-src",
        "script-src",
        "style-src",
        "font-src",
        "img-src",
        "object-src",
        "connect-src",
        "frame-ancestors",
        "worker-src",
    ]
    # Check if all expected CSP directives are present
    for directive in expected_directives:
        assert f"{directive}" in csp_header, f"Missing directive: {directive}"
