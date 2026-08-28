import json

import pytest
from allauth.account.models import EmailAddress, EmailConfirmation
from django.utils import timezone

from config import hosts
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.models import User

pytestmark = pytest.mark.django_db

SIGNUP_URL = "/api/auth/signup/"
CONFIRM_EMAIL_URL = "/api/auth/confirm-email/"
LOGIN_URL = "/api/auth/login/"
PASSWORD = "a very Long and compl1c@ted phrase"


def _developer_payload(**overrides):
    payload = {
        "email": "consumer@example.com",
        "password1": PASSWORD,
        "password2": PASSWORD,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "dev_organisation": "Analytical Engines",
        "description": "A journey planner for local bus services.",
        "intended_use": 1,
        "national_interest": False,
        "regional_areas": "Here and there",
        "share_app_usage": True,
        "opt_in_user_research": True,
    }
    payload.update(overrides)
    return payload


def _post(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def _unverified_confirmation(user):
    email_address, _ = EmailAddress.objects.get_or_create(
        user=user, email=user.email, defaults={"primary": True}
    )
    email_address.verified = False
    email_address.save(update_fields=["verified"])
    confirmation = EmailConfirmation.create(email_address)
    confirmation.sent = timezone.now()
    confirmation.save()
    return confirmation


def test_signup_creates_an_unverified_developer_account(client_factory):
    client = client_factory(host=hosts.DATA_HOST)

    response = _post(client, SIGNUP_URL, _developer_payload())

    assert response.status_code == 201
    assert response.json() == {
        "account_exists": False,
        "email": "consumer@example.com",
    }

    user = User.objects.get(email="consumer@example.com")
    assert user.account_type == AccountType.developer.value
    assert user.first_name == "Ada"
    assert user.dev_organisation == "Analytical Engines"
    assert user.settings.intended_use == 1
    assert not EmailAddress.objects.get(user=user).verified


def test_signup_returns_field_errors_for_the_developer_form(client_factory):
    client = client_factory(host=hosts.DATA_HOST)

    response = _post(
        client,
        SIGNUP_URL,
        {"email": "consumer@example.com", "password1": PASSWORD},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "Validation failed"
    assert set(body["field_errors"]) >= {
        "first_name",
        "last_name",
        "dev_organisation",
        "description",
        "intended_use",
        "national_interest",
        "share_app_usage",
        "opt_in_user_research",
        "password2",
    }
    assert not User.objects.filter(email="consumer@example.com").exists()


def test_signup_reports_an_existing_account_without_creating_a_duplicate(
    client_factory,
):
    UserFactory(email="consumer@example.com")
    client = client_factory(host=hosts.DATA_HOST)

    response = _post(client, SIGNUP_URL, _developer_payload())

    assert response.status_code == 200
    assert response.json() == {"account_exists": True}
    assert User.objects.filter(email="consumer@example.com").count() == 1


def test_confirm_email_verifies_the_address(client_factory):
    user = UserFactory(email="consumer@example.com")
    confirmation = _unverified_confirmation(user)
    client = client_factory(host=hosts.DATA_HOST)

    response = _post(client, CONFIRM_EMAIL_URL, {"key": confirmation.key})

    assert response.status_code == 200
    assert response.json() == {"email": "consumer@example.com"}
    assert EmailAddress.objects.get(user=user).verified


def test_login_get_returns_the_email_stashed_by_confirm(client_factory):
    user = UserFactory(email="consumer@example.com")
    confirmation = _unverified_confirmation(user)
    client = client_factory(host=hosts.DATA_HOST)

    assert (
        _post(client, CONFIRM_EMAIL_URL, {"key": confirmation.key}).status_code == 200
    )

    response = client.get(LOGIN_URL)

    assert response.status_code == 200
    assert response.json() == {"verifiedEmail": "consumer@example.com"}
    assert client.get(LOGIN_URL).json() == {"verifiedEmail": None}


def test_confirm_email_rejects_a_key_that_has_already_been_used(client_factory):
    """Allauth only treats confirmations of unverified addresses as valid, so a
    second click on the same link is an invalid link, as it is in Django."""
    user = UserFactory(email="consumer@example.com")
    confirmation = _unverified_confirmation(user)
    client = client_factory(host=hosts.DATA_HOST)

    assert (
        _post(client, CONFIRM_EMAIL_URL, {"key": confirmation.key}).status_code == 200
    )

    response = _post(client, CONFIRM_EMAIL_URL, {"key": confirmation.key})

    assert response.status_code == 400
    assert "expired or is invalid" in response.json()["detail"]


def test_confirm_email_rejects_an_unknown_key(client_factory):
    client = client_factory(host=hosts.DATA_HOST)

    response = _post(client, CONFIRM_EMAIL_URL, {"key": "not-a-real-key"})

    assert response.status_code == 400
    assert "expired or is invalid" in response.json()["detail"]


def test_signup_and_confirm_email_are_available_on_the_publish_host(client_factory):
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post(client, CONFIRM_EMAIL_URL, {"key": "not-a-real-key"})

    assert response.status_code == 400
