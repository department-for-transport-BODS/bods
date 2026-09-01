import json

import pytest

from config import hosts
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserFactory,
    AgentUserInviteFactory,
    InvitationFactory,
    OrgAdminFactory,
    OrgStaffFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite, Invitation

pytestmark = pytest.mark.django_db


def _post(client, url, **body):
    return client.post(url, data=json.dumps(body), content_type="application/json")


@pytest.fixture
def org_admin_client(client_factory):
    organisation = OrganisationFactory()
    admin = OrgAdminFactory(organisations=(organisation,))
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=admin)
    return client, organisation, admin


def test_members_list_requires_authentication(client_factory):
    organisation = OrganisationFactory()
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = client.get(f"/api/organisation/{organisation.id}/members/")

    assert response.status_code == 401


def test_members_list_is_forbidden_for_another_org_admin(
    org_admin_client, client_factory
):
    _client, organisation, _admin = org_admin_client
    other_org = OrganisationFactory()
    other_admin = OrgAdminFactory(organisations=(other_org,))
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=other_admin)

    response = client.get(f"/api/organisation/{organisation.id}/members/")

    assert response.status_code == 403


def test_members_list_is_forbidden_for_org_staff(client_factory):
    organisation = OrganisationFactory()
    staff = OrgStaffFactory(organisations=(organisation,))
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=staff)

    response = client.get(f"/api/organisation/{organisation.id}/members/")

    assert response.status_code == 403


def test_members_list_includes_pending_agent_email(org_admin_client):
    client, organisation, admin = org_admin_client
    invitation = InvitationFactory(
        email="new.agent@example.com",
        account_type=AccountType.agent_user.value,
        organisation=organisation,
        inviter=admin,
        accepted=False,
    )
    AgentUserInviteFactory(
        agent=None,
        invitation=invitation,
        organisation=organisation,
        inviter=admin,
        status=AgentUserInvite.PENDING,
    )

    response = client.get(f"/api/organisation/{organisation.id}/members/")

    assert response.status_code == 200
    pending = response.json()["pendingAgentInvites"]
    assert len(pending) == 1
    assert pending[0]["email"] == "new.agent@example.com"
    assert pending[0]["organisationName"] == organisation.name


def test_invite_is_forbidden_for_another_org_admin(org_admin_client, client_factory):
    _client, organisation, _admin = org_admin_client
    other_org = OrganisationFactory()
    other_admin = OrgAdminFactory(organisations=(other_org,))
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=other_admin)

    response = _post(
        client,
        f"/api/organisation/{organisation.id}/invite/",
        email="staff@example.com",
        accountType="staff",
    )

    assert response.status_code == 403
    assert not Invitation.objects.filter(email="staff@example.com").exists()


def test_invite_creates_a_pending_staff_invitation(org_admin_client, mailoutbox):
    client, organisation, _admin = org_admin_client

    response = _post(
        client,
        f"/api/organisation/{organisation.id}/invite/",
        email="staff@example.com",
        accountType="staff",
    )

    assert response.status_code == 201
    invitation = Invitation.objects.get(email="staff@example.com")
    assert invitation.organisation_id == organisation.id
    assert invitation.account_type == AccountType.org_staff.value
    assert invitation.accepted is False
    assert mailoutbox[0].to[0] == "staff@example.com"


def test_set_active_cannot_deactivate_self(org_admin_client):
    client, _organisation, admin = org_admin_client

    response = _post(
        client,
        f"/api/organisation/members/{admin.id}/set-active/",
        isActive=False,
    )

    assert response.status_code == 404
    admin.refresh_from_db()
    assert admin.is_active is True


def test_set_active_cannot_target_another_orgs_member(org_admin_client):
    client, _organisation, _admin = org_admin_client
    other_staff = OrgStaffFactory()

    response = _post(
        client,
        f"/api/organisation/members/{other_staff.id}/set-active/",
        isActive=False,
    )

    assert response.status_code == 404
    other_staff.refresh_from_db()
    assert other_staff.is_active is True


def test_agent_invite_is_hidden_from_unrelated_users(org_admin_client, client_factory):
    _client, organisation, admin = org_admin_client
    other_org = OrganisationFactory()
    agent = AgentUserFactory(organisations=(other_org,))
    invite = AgentUserInviteFactory(
        agent=agent,
        organisation=organisation,
        inviter=admin,
        status=AgentUserInvite.PENDING,
    )
    stranger = UserFactory()
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=stranger)

    response = client.get(f"/api/auth/agent/invite/{invite.id}/")

    assert response.status_code == 404


def test_agent_cannot_respond_to_another_agents_invite(
    org_admin_client, client_factory
):
    _client, organisation, admin = org_admin_client
    home_org = OrganisationFactory()
    agent = AgentUserFactory(organisations=(home_org,))
    invite = AgentUserInviteFactory(
        agent=agent,
        organisation=organisation,
        inviter=admin,
        status=AgentUserInvite.PENDING,
    )
    other_agent = AgentUserFactory()
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=other_agent)

    response = _post(
        client,
        f"/api/auth/agent/invite/{invite.id}/respond/",
        status=AgentUserInvite.ACCEPTED,
    )

    assert response.status_code == 404
    invite.refresh_from_db()
    assert invite.status == AgentUserInvite.PENDING


def test_agent_can_leave_an_accepted_organisation(org_admin_client, client_factory):
    _client, organisation, admin = org_admin_client
    home_org = OrganisationFactory()
    agent = AgentUserFactory(organisations=(home_org,))
    invite = AgentUserInviteFactory(
        agent=agent,
        organisation=organisation,
        inviter=admin,
        status=AgentUserInvite.ACCEPTED,
    )
    agent.organisations.add(organisation)
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=agent)

    response = _post(client, f"/api/auth/agent/invite/{invite.id}/leave/")

    assert response.status_code == 200
    invite.refresh_from_db()
    assert invite.status == AgentUserInvite.INACTIVE
    assert organisation not in agent.organisations.all()


def test_remove_agent_is_forbidden_for_org_staff(client_factory):
    organisation = OrganisationFactory()
    admin = OrgAdminFactory(organisations=(organisation,))
    staff = OrgStaffFactory(organisations=(organisation,))
    home_org = OrganisationFactory()
    agent = AgentUserFactory(organisations=(home_org,))
    invite = AgentUserInviteFactory(
        agent=agent,
        organisation=organisation,
        inviter=admin,
        status=AgentUserInvite.ACCEPTED,
    )
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=staff)

    response = _post(client, f"/api/auth/agent/invite/{invite.id}/remove/")

    assert response.status_code == 403
    invite.refresh_from_db()
    assert invite.status == AgentUserInvite.ACCEPTED
