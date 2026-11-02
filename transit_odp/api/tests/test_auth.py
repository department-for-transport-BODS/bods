import json
import re

from allauth.account.models import EmailAddress
from django.core.cache import cache
from django.test import override_settings
import pytest
from rest_framework.exceptions import Throttled

from config import hosts
from transit_odp.api.views.auth import LoginAPIView, _serialize_user
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import AgentUserFactory, UserFactory


pytestmark = pytest.mark.django_db

NEW_PASSWORD = "newPassword_34324()()"
LOGIN_URL = "/api/auth/login/"


def _post_login(client, payload):
    return client.post(
        LOGIN_URL,
        data=json.dumps(payload),
        content_type="application/json",
    )


@pytest.mark.parametrize(
    ("payload", "field_errors"),
    [
        (
            {"email": "", "password": ""},
            {
                "email": ["Please provide an email"],
                "password": ["Please provide a password"],
            },
        ),
        (
            {"email": "person@example.com", "password": ""},
            {"password": ["Please provide a password"]},
        ),
        (
            {"email": "", "password": "password"},
            {"email": ["Please provide an email"]},
        ),
        (
            {"email": "not-an-email", "password": "password"},
            {
                "email": [
                    "Enter an email address in the right format, like name@example.com"
                ]
            },
        ),
    ],
)
@override_settings(ACCOUNT_LOGIN_ATTEMPTS_LIMIT=100)
def test_login_api_returns_django_login_form_validation_messages(
    client_factory, payload, field_errors
):
    cache.clear()
    client = client_factory(host=hosts.DATA_HOST)

    response = _post_login(client, payload)

    assert response.status_code == 400
    assert response.json() == {"field_errors": field_errors}


@override_settings(ACCOUNT_LOGIN_ATTEMPTS_LIMIT=100)
def test_login_api_returns_django_invalid_credentials_message(client_factory):
    cache.clear()
    client = client_factory(host=hosts.DATA_HOST)

    response = _post_login(
        client,
        {"email": "unknown-dbods-2740@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "The email address and/or password you specified are not correct."
    }


@override_settings(ACCOUNT_LOGIN_ATTEMPTS_LIMIT=100)
def test_login_api_returns_django_unverified_email_message(
    client_factory, mailoutbox
):
    cache.clear()
    email = "unverified-dbods-2740@example.com"
    password = "Correct-password-123!"
    user = UserFactory.create(email=email, password=password, verified=False)
    EmailAddress.objects.create(
        user=user,
        email=email,
        verified=False,
        primary=True,
    )
    client = client_factory(host=hosts.DATA_HOST)

    response = _post_login(client, {"email": email, "password": password})

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            f"The email address {email} has not yet been verified. "
            "We have sent you another confirmation email."
        )
    }
    assert mailoutbox[0].to == [email]


@override_settings(ACCOUNT_LOGIN_ATTEMPTS_LIMIT=100)
def test_login_api_routes_inactive_accounts_to_django_inactive_page(client_factory):
    cache.clear()
    email = "inactive-dbods-2740@example.com"
    password = "Correct-password-123!"
    UserFactory.create(
        email=email,
        password=password,
        is_active=False,
        verified=True,
    )
    client = client_factory(host=hosts.DATA_HOST)

    response = _post_login(client, {"email": email, "password": password})

    assert response.status_code == 403
    assert response.json()["code"] == "account_inactive"
    assert response.json()["detail"] == (
        "Your account is inactive and you no longer have access to the "
        "Bus Open Data Service. If you were not expecting this then please "
        "contact us."
    )


def test_login_api_throttle_uses_django_login_message():
    with pytest.raises(Throttled) as throttled:
        LoginAPIView().throttled(None, 1)

    assert throttled.value.status_code == 429
    assert throttled.value.detail == "Too many failed login attempts. Try again later."
    assert throttled.value.wait == 1


@override_settings(ACCOUNT_LOGIN_ATTEMPTS_LIMIT=1, ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT=900)
def test_login_api_returns_django_message_when_rate_limited(client_factory):
    cache.clear()
    client = client_factory(host=hosts.DATA_HOST)
    payload = {"email": "unknown-dbods-2740@example.com", "password": "wrong-password"}

    first_response = _post_login(client, payload)
    throttled_response = _post_login(client, payload)

    assert first_response.status_code == 400
    assert throttled_response.status_code == 429
    assert throttled_response.json() == {
        "detail": "Too many failed login attempts. Try again later."
    }


def test_serialize_user_includes_routing_fields_for_org_user():
    organisation = OrganisationFactory()
    user = UserFactory(
        account_type=AccountType.org_admin.value,
        organisations=(organisation,),
    )

    payload = _serialize_user(user)

    assert payload["account_type"] == AccountType.org_admin.value
    assert payload["organisation_id"] == organisation.id
    assert payload["is_org_user"] is True
    assert payload["is_single_org_user"] is True
    assert payload["is_agent_user"] is False


def test_serialize_user_includes_routing_fields_for_agent_user():
    organisation = OrganisationFactory()
    user = AgentUserFactory(organisations=(organisation,))

    payload = _serialize_user(user)

    assert payload["account_type"] == AccountType.agent_user.value
    assert payload["organisation_id"] == organisation.id
    assert payload["is_org_user"] is True
    assert payload["is_single_org_user"] is False
    assert payload["is_agent_user"] is True


PASSWORD_CHANGE_URL = "/api/auth/password/change/"


def _post_password_change(client, payload):
    return client.post(
        PASSWORD_CHANGE_URL,
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_password_change_requires_authentication(client_factory):
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post_password_change(
        client,
        {
            "oldpassword": "oldpassword",
            "password1": NEW_PASSWORD,
            "password2": NEW_PASSWORD,
        },
    )

    assert response.status_code == 403


def test_password_change_rejects_incorrect_current_password(user, client_factory):
    user.set_password("oldpassword")
    user.save()
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)

    response = _post_password_change(
        client,
        {
            "oldpassword": "not-the-password",
            "password1": NEW_PASSWORD,
            "password2": NEW_PASSWORD,
        },
    )

    assert response.status_code == 400
    assert "oldpassword" in response.json()["field_errors"]
    user.refresh_from_db()
    assert user.check_password("oldpassword")


def test_password_change_updates_password_and_sends_email(
    user, client_factory, mailoutbox
):
    user.set_password("oldpassword")
    user.save()
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)

    response = _post_password_change(
        client,
        {
            "oldpassword": "oldpassword",
            "password1": NEW_PASSWORD,
            "password2": NEW_PASSWORD,
        },
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)
    assert mailoutbox[0].to[0] == user.email
    assert (
        mailoutbox[0].subject
        == "You have changed your password on the Bus Open Data Service"
    )

    session_response = client.get("/api/auth/user/")
    assert session_response.status_code == 200
    assert session_response.json()["id"] == user.id


PASSWORD_RESET_URL = "/api/auth/password/reset/"
PASSWORD_RESET_KEY_URL = "/api/auth/password/reset/key/"


def _post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def _reset_key_from_mailbox(mailoutbox):
    match = re.search(
        r"/account/password/reset/key/([^/\s]+)/?",
        mailoutbox[0].body,
    )
    assert match is not None
    uidb36, key = match.group(1).split("-", 1)
    return uidb36, key


def test_password_reset_does_not_send_mail_for_unknown_email(
    client_factory, mailoutbox
):
    client = client_factory(host=hosts.DATA_HOST)

    response = _post_json(client, PASSWORD_RESET_URL, {"email": "nobody@example.com"})

    assert response.status_code == 200
    assert response.json()["email"] == "nobody@example.com"
    assert mailoutbox == []


def test_password_reset_sends_link_and_sets_new_password(
    user, client_factory, mailoutbox
):
    client = client_factory(host=hosts.DATA_HOST)
    user.set_password("oldpassword")
    user.save()

    response = _post_json(client, PASSWORD_RESET_URL, {"email": user.email})

    assert response.status_code == 200
    assert response.json()["email"] == user.email
    assert mailoutbox[0].to[0] == user.email
    assert mailoutbox[0].subject == "Change your password on the Bus Open Data Service"

    uidb36, key = _reset_key_from_mailbox(mailoutbox)

    valid = client.get(PASSWORD_RESET_KEY_URL, data={"uidb36": uidb36, "key": key})
    assert valid.status_code == 200
    assert valid.json()["valid"] is True

    reset = _post_json(
        client,
        PASSWORD_RESET_KEY_URL,
        {
            "uidb36": uidb36,
            "key": key,
            "password1": NEW_PASSWORD,
            "password2": NEW_PASSWORD,
        },
    )

    assert reset.status_code == 200
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)

    session_response = client.get("/api/auth/user/")
    assert session_response.status_code == 200
    assert session_response.json()["id"] == user.id


def test_password_reset_rejects_an_invalid_key(client_factory):
    client = client_factory(host=hosts.DATA_HOST)

    response = _post_json(
        client,
        PASSWORD_RESET_KEY_URL,
        {
            "uidb36": "MQ",
            "key": "not-a-real-key",
            "password1": NEW_PASSWORD,
            "password2": NEW_PASSWORD,
        },
    )

    assert response.status_code == 400
    assert "expired or is invalid" in response.json()["detail"]
