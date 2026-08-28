import json

import pytest

from config import hosts
from transit_odp.api.views.auth import _serialize_user
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import AgentUserFactory, UserFactory


pytestmark = pytest.mark.django_db

NEW_PASSWORD = "newPassword_34324()()"


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
