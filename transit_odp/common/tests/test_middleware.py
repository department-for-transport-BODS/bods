from random import choices
from string import ascii_letters

import pytest
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
        "worker-src",
    ]
    # Check if all expected CSP directives are present
    for directive in expected_directives:
        assert f"{directive}" in csp_header, f"Missing directive: {directive}"
