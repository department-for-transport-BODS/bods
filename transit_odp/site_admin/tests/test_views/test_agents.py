import pytest
from django.contrib.auth import get_user_model
from django_hosts.resolvers import reverse

from config.hosts import ADMIN_HOST
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.site_admin.views import RemoveAgentUserView
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserFactory,
    AgentUserInviteFactory,
    InvitationFactory,
    OrgAdminFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.views.mixins import SiteAdminViewMixin

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestAgentDetailView:
    host = ADMIN_HOST

    def setup_agent(self):
        AgentUserFactory.create_batch(2, is_active=False)
        OrganisationFactory.create_batch(2, is_active=False)
        orgs = OrganisationFactory.create_batch(5)
        return AgentUserFactory.create(organisations=orgs)

    def test_standard_user_cant_access(self, client_factory):
        agent = self.setup_agent()
        url = reverse("users:agent-detail", kwargs={"pk": agent.id}, host=self.host)
        client = client_factory(host=self.host)
        user = OrgAdminFactory.create()
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 403

    def test_site_admin_get_agent_detail(self, client_factory, user_factory):
        user = user_factory(account_type=AccountType.site_admin.value)
        client = client_factory(host=self.host)
        agent = self.setup_agent()
        client.force_login(user=user)
        url = reverse("users:agent-detail", kwargs={"pk": agent.id}, host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        table = response.context["table"]
        assert len(table.rows) == 5

    def test_site_admin_gets_404_when_agent_doesnt_exist(
        self, client_factory, user_factory
    ):
        user = user_factory(account_type=AccountType.site_admin.value)
        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("users:agent-detail", kwargs={"pk": 999}, host=self.host)
        response = client.get(url)
        assert response.status_code == 404


class TestAgentListView:
    host = ADMIN_HOST
    url = reverse("users:agent-list", host=host)

    def test_standard_user_cant_access(self, client_factory):
        client = client_factory(host=self.host)
        user = OrgAdminFactory.create()
        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 403

    def test_site_admin_get_agent_list(self, client_factory, user_factory):
        user = user_factory(account_type=AccountType.site_admin.value)
        client = client_factory(host=self.host)
        AgentUserFactory.create_batch(4)
        AgentUserFactory.create_batch(2, is_active=False)
        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 200
        table = response.context["table"]
        assert len(table.rows) == 4


class TestAgentUserInviteDetails:
    host = ADMIN_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(RemoveAgentUserView, SiteAdminViewMixin)

    def test_correct_template_used(self, client_factory, user_factory):
        user = user_factory(account_type=AccountType.site_admin.value)
        organisation = OrganisationFactory.create()
        agent = UserFactory.create(
            email="abc@abc.com",
            organisations=(organisation,),
            account_type=AccountType.agent_user.value,
        )
        invite = AgentUserInviteFactory(
            organisation=organisation, agent=agent, status=AgentUserInvite.ACCEPTED
        )

        url = reverse(
            "users:org-remove-agent",
            kwargs={"pk": organisation.id, "pk1": agent.id, "invite_id": invite.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)

        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/remove_agent_user_from_org.html" in [
            t.name for t in response.templates
        ]
        assert response.context["object"].agent.email == agent.email

    def test_user_does_not_exist(self, client_factory, user_factory):
        # Set up
        user = user_factory(account_type=AccountType.site_admin.value)
        organisation = OrganisationFactory.create()

        agent = UserFactory.create(
            id=5,
            email="abc@abc.com",
            organisations=(organisation,),
            account_type=AccountType.agent_user.value,
        )
        AgentUserInviteFactory(id=20, agent=agent, organisation=organisation)

        url = reverse(
            "users:org-remove-agent",
            kwargs={"pk": organisation.id, "pk1": 5, "invite_id": 21},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)

        response = client.get(url)
        assert response.status_code == 404


class TestResendAgentUserInviteDetail:
    host = ADMIN_HOST

    def test_admin_can_resend_for_pending_agent(self, client_factory, user_factory):
        user = user_factory(account_type=AccountType.site_admin.value)
        organisation = OrganisationFactory.create()
        standard_invite = InvitationFactory()
        invite = AgentUserInviteFactory(
            organisation=organisation,
            agent=None,
            status=AgentUserInvite.PENDING,
            invitation=standard_invite,
        )

        url = reverse(
            "users:org-resend-agent-invite",
            kwargs={"pk": organisation.id, "invite_id": invite.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/resend_agent_invite.html" in [
            t.name for t in response.templates
        ]
        assert response.context["agentuserinvite"].email == standard_invite.email

    def test_admin_cant_resend_for_accepted_agent(self, client_factory, user_factory):
        user = user_factory(account_type=AccountType.site_admin.value)
        organisation = OrganisationFactory.create()
        standard_invite = InvitationFactory()
        agent = UserFactory.create(
            email="abc@abc.com",
            organisations=(organisation,),
            account_type=AccountType.agent_user.value,
        )
        invite = AgentUserInviteFactory(
            organisation=organisation,
            agent=agent,
            status=AgentUserInvite.ACCEPTED,
            invitation=standard_invite,
        )

        url = reverse(
            "users:org-resend-agent-invite",
            kwargs={"pk": organisation.id, "invite_id": invite.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        response = client.get(url)

        assert response.status_code == 404

    def test_admin_can_access_success_page(self, client_factory, user_factory):
        user = user_factory(account_type=AccountType.site_admin.value)
        organisation = OrganisationFactory.create()
        standard_invite = InvitationFactory()
        invite = AgentUserInviteFactory(
            organisation=organisation,
            agent=None,
            status=AgentUserInvite.PENDING,
            invitation=standard_invite,
        )

        url = reverse(
            "users:org-resend-agent-invite-success",
            kwargs={"pk": organisation.id, "invite_id": invite.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/resend_agent_invite_success.html" in [
            t.name for t in response.templates
        ]
        assert response.context["agentuserinvite"].email == standard_invite.email
