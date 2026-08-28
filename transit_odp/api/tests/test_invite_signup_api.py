import json
from datetime import timedelta

import pytest
from allauth.account.models import EmailAddress
from django.utils import timezone

from config import hosts
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserInviteFactory,
    InvitationFactory,
    OrgAdminFactory,
)
from transit_odp.users.models import AgentUserInvite, Invitation, User

pytestmark = pytest.mark.django_db

ACCEPT_URL = "/api/auth/invite/accept/"
SIGNUP_URL = "/api/auth/signup/"
PASSWORD = "a very Long and compl1c@ted phrase"


def _post(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type="application/json")


def _operator_invite(**overrides):
    organisation = OrganisationFactory()
    admin = OrgAdminFactory(organisations=(organisation,))
    defaults = {
        "email": "new.operator@example.com",
        "account_type": AccountType.org_admin.value,
        "organisation": organisation,
        "inviter": admin,
        "accepted": False,
    }
    defaults.update(overrides)
    return InvitationFactory(**defaults), organisation


def _agent_invite(**overrides):
    invitation, organisation = _operator_invite(
        email="new.agent@example.com",
        account_type=AccountType.agent_user.value,
        **overrides,
    )
    AgentUserInviteFactory(
        agent=None,
        invitation=invitation,
        organisation=organisation,
        inviter=invitation.inviter,
        status=AgentUserInvite.PENDING,
    )
    return invitation, organisation


def test_signup_get_is_developer_mode_without_an_invite(client_factory):
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = client.get(SIGNUP_URL)

    assert response.status_code == 200
    assert response.json() == {"mode": "developer"}


def test_accept_invite_stashes_operator_signup(client_factory):
    invitation, organisation = _operator_invite()
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post(client, ACCEPT_URL, {"key": invitation.key})

    assert response.status_code == 200
    assert response.json() == {
        "email": "new.operator@example.com",
        "isAgent": False,
        "organisationName": organisation.name,
    }

    invitation.refresh_from_db()
    assert invitation.accepted is False

    status_response = client.get(SIGNUP_URL)
    assert status_response.json() == {
        "mode": "operator",
        "email": "new.operator@example.com",
        "organisationName": organisation.name,
    }


def test_accept_invite_stashes_agent_signup(client_factory):
    invitation, organisation = _agent_invite()
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post(client, ACCEPT_URL, {"key": invitation.key})

    assert response.status_code == 200
    assert response.json() == {
        "email": "new.agent@example.com",
        "isAgent": True,
        "organisationName": organisation.name,
    }
    assert client.get(SIGNUP_URL).json()["mode"] == "agent"


def test_accept_invite_rejects_an_unknown_key(client_factory):
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post(client, ACCEPT_URL, {"key": "not-a-real-invitation-key"})

    assert response.status_code == 410
    body = response.json()
    assert body["expired"] is True
    assert "expired" in body["detail"]


def test_accept_invite_rejects_an_already_accepted_invite(client_factory):
    invitation, _organisation = _operator_invite(accepted=True)
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post(client, ACCEPT_URL, {"key": invitation.key})

    assert response.status_code == 410
    assert response.json()["expired"] is True


def test_accept_invite_rejects_an_expired_invite(client_factory):
    invitation, _organisation = _operator_invite()
    invitation.sent = timezone.now() - timedelta(days=4)
    invitation.save()
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post(client, ACCEPT_URL, {"key": invitation.key})

    assert response.status_code == 410
    assert response.json()["expired"] is True


def test_operator_signup_after_accept_creates_an_org_user(client_factory):
    invitation, organisation = _operator_invite()
    client = client_factory(host=hosts.PUBLISH_HOST)
    assert _post(client, ACCEPT_URL, {"key": invitation.key}).status_code == 200

    response = _post(
        client,
        SIGNUP_URL,
        {
            "email": "tampered@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
            "opt_in_user_research": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["account_exists"] is False
    assert body["email"] == "new.operator@example.com"
    assert body["user"]["email"] == "new.operator@example.com"
    assert body["user"]["account_type"] == AccountType.org_admin.value

    user = User.objects.get(email="new.operator@example.com")
    assert user.account_type == AccountType.org_admin.value
    assert list(user.organisations.all()) == [organisation]
    assert EmailAddress.objects.get(user=user).verified
    assert client.get("/api/auth/user/").status_code == 200

    invitation.refresh_from_db()
    assert invitation.accepted is True
    assert not User.objects.filter(email="tampered@example.com").exists()


def test_agent_signup_after_accept_sets_agent_organisation(client_factory):
    invitation, organisation = _agent_invite()
    client = client_factory(host=hosts.PUBLISH_HOST)
    assert _post(client, ACCEPT_URL, {"key": invitation.key}).status_code == 200

    response = _post(
        client,
        SIGNUP_URL,
        {
            "email": invitation.email,
            "agent_organisation": "Coach Consultants",
            "password1": PASSWORD,
            "password2": PASSWORD,
            "opt_in_user_research": False,
        },
    )

    assert response.status_code == 201
    user = User.objects.get(email="new.agent@example.com")
    assert user.account_type == AccountType.agent_user.value
    assert user.agent_organisation == "Coach Consultants"
    assert organisation in user.organisations.all()

    agent_invite = AgentUserInvite.objects.get(invitation=invitation)
    assert agent_invite.agent == user
    assert agent_invite.status == AgentUserInvite.ACCEPTED

    invitation.refresh_from_db()
    assert invitation.accepted is True


def test_operator_signup_without_accept_still_uses_the_developer_form(client_factory):
    invitation, _organisation = _operator_invite()
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = _post(
        client,
        SIGNUP_URL,
        {
            "email": invitation.email,
            "password1": PASSWORD,
            "password2": PASSWORD,
            "opt_in_user_research": True,
        },
    )

    assert response.status_code == 400
    assert "first_name" in response.json()["field_errors"]
    assert not User.objects.filter(email=invitation.email).exists()
    assert Invitation.objects.get(pk=invitation.pk).accepted is False
