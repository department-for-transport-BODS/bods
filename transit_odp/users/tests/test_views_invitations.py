from datetime import datetime, timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils import timezone
from django_hosts.resolvers import get_host, reverse

import config.hosts
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType, AgentUserType
from transit_odp.users.factories import (
    AgentUserInviteFactory,
    InvitationFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite, Invitation
from transit_odp.users.views.invitations import AcceptInvite
from django.conf import settings

pytestmark = pytest.mark.django_db


class TestAcceptInvite:
    def test_view_initialises_invitation_started_state(
        self, mocker, rf: RequestFactory
    ):
        """Tests that the view initialises the invitation_started state"""
        # Setup
        request = rf.get("fake-url/")
        request.user = AnonymousUser()
        invitation = InvitationFactory.create(accepted=False)

        view = AcceptInvite()
        view.request = request

        # mocker out adapter. Note we have to mock out property on class not instance
        mocked_adapter = mocker.patch.object(AcceptInvite, "adapter")

        # mock out call to superclass
        mocker.patch(
            "transit_odp.users.views.invitations.AcceptInvite.get_object",
            return_value=invitation,
        )
        mocker.patch(
            "transit_odp.users.views.invitations.AcceptInviteBase.post",
            return_value=None,
        )

        # Test
        view.post()

        # Assert
        assert mocked_adapter.unstash_invitation_started.called_once_with(request)

    def test_view_returns_410_when_invitation_already_accepted(
        self, mocker, rf: RequestFactory
    ):
        """Tests that the view returns invitation_expired.html when an invitation is
        already accepted"""
        # Setup
        host = get_host(config.hosts.PUBLISH_HOST)
        request = rf.get("fake-url/")
        request.user = AnonymousUser()

        mocked_site = mocker.Mock()
        mocked_site.name = "Publish Data Service"
        request.site = mocked_site

        request.host = host
        request.META['HTTP_HOST'] = f"{settings.PUBLISH_SUBDOMAIN}.{settings.PARENT_HOST}"

        invitation = InvitationFactory.create(accepted=True)

        view = AcceptInvite()
        view.request = request
        view.context_object_name = {}

        # mock out call to AcceptInvite and superclass
        mocker.patch(
            "transit_odp.users.views.invitations.AcceptInvite.get_object",
            return_value=invitation,
        )
        mocked_render = mocker.patch(
            "django.shortcuts.render",
            return_value=None,
        )
        mocker.patch(
            "transit_odp.users.views.invitations.AcceptInviteBase.post",
            return_value=None,
        )

        # Test
        view.post()

        # Assert
        assert mocked_render.called_once_with(
            request, "users/invitation_expired.html", context={}
        )

    def test_view_returns_410_when_invitation_expired(self, mocker, rf: RequestFactory):
        """Tests that the view returns invitation_expired.html when an invitation is
        expired"""
        # Setup
        host = get_host(config.hosts.PUBLISH_HOST)
        request = rf.get("fake-url/")
        request.user = AnonymousUser()

        mocked_site = mocker.Mock()
        mocked_site.name = "Publish Data Service"
        request.site = mocked_site

        request.host = host
        request.META['HTTP_HOST'] = f"{settings.PUBLISH_SUBDOMAIN}.{settings.PARENT_HOST}"

        invitation = InvitationFactory.create(
            accepted=False,
            sent=timezone.now() - timedelta(days=4),  # invitation expiry is 3 days
        )

        view = AcceptInvite()
        view.request = request
        view.context_object_name = {}

        # mock out call to AcceptInvite and superclass
        mocker.patch(
            "transit_odp.users.views.invitations.AcceptInvite.get_object",
            return_value=invitation,
        )
        mocked_render = mocker.patch(
            "django.shortcuts.render",
            return_value=None,
        )
        mocker.patch(
            "transit_odp.users.views.invitations.AcceptInviteBase.post",
            return_value=None,
        )

        # Test
        view.post()

        # Assert
        assert mocked_render.called_once_with(
            request, "users/invitation_expired.html", context={}
        )


class TestSendInvite:
    """
    Groups together all the tests for the send invite page ie inviting
    org admin, org staff and agents. Please note the following:
      * On success, user is redirected. If response is 200, validation errors have
        been added to the page.
      * object manager .get() will throw error if number of returned objects is > 1
    """

    host = config.hosts.PUBLISH_HOST
    url = reverse("users:invite", host=host)

    def test_invitation_created(self, client_factory):
        client = client_factory(host=self.host)
        admin = UserFactory(account_type=AccountType.org_admin.value)
        client.force_login(user=admin)

        email = "test@test.com"
        response = client.post(
            self.url,
            data={
                "email": email,
                "selected_item": "staff",
                "account_type": AccountType.developer.value,
            },
        )

        assert response.status_code == 302
        invite = Invitation.objects.get(email=email)
        assert invite.is_key_contact is False
        assert invite.sent
        assert AgentUserInvite.objects.count() == 0

    def test_new_agent_invitations_created(self, client_factory, mailoutbox):
        client = client_factory(host=self.host)
        org = OrganisationFactory.create()
        admin = UserFactory(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        client.force_login(user=admin)

        email = "test@test.com"
        response = client.post(
            self.url,
            data={
                "email": email,
                "selected_item": "agent",
                "account_type": AccountType.developer.value,
            },
        )

        assert response.status_code == 302
        agent_invite = AgentUserInvite.objects.get(inviter=admin)
        invite = agent_invite.invitation
        assert invite is not None
        assert (
            mailoutbox[-1].subject
            == f"{org.name} has invited you to act as an agent on behalf of them"
        )
        assert (
            reverse(
                "invitations:accept-invite",
                args=[invite.key],
                host=config.hosts.PUBLISH_HOST,
            )
            in mailoutbox[-1].body
        )

    def test_existing_agent_invitations_created(self, client_factory, mailoutbox):
        client = client_factory(host=self.host)
        org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        our_hero = UserFactory.create(account_type=AccountType.agent_user.value)
        client.force_login(user=admin)

        response = client.post(
            self.url,
            data={
                "email": our_hero.email,
                "selected_item": "agent",
                "account_type": AccountType.developer.value,
            },
        )

        assert response.status_code == 302
        agent_invite = AgentUserInvite.objects.get(agent_id=our_hero.id)
        assert agent_invite.invitation is None
        assert (
            mailoutbox[-1].subject
            == f"{org.name} has invited you to act as an agent on behalf of them"
        )
        assert (
            reverse("users:home", host=config.hosts.PUBLISH_HOST) in mailoutbox[-1].body
        )

    def test_existing_user_error(self, client_factory):

        client = client_factory(host=self.host)
        admin = UserFactory.create(account_type=AccountType.org_admin.value)
        our_hero = UserFactory.create(account_type=AccountType.org_admin.value)
        client.force_login(user=admin)

        response = client.post(
            self.url,
            data={
                "email": our_hero.email,
                "selected_item": "agent",
                "account_type": AccountType.developer.value,
            },
        )

        assert response.status_code == 200
        assert (
            response.context_data["form"].errors["email"][0]
            == "An active non-agent user is using this e-mail address"
        )

    @pytest.mark.parametrize(
        "account_type,frontend",
        [
            (AccountType.agent_user.value, "agent"),
            (AccountType.org_staff.value, "staff"),
            (AccountType.org_admin.value, "admin"),
        ],
    )
    def test_existing_invite_error(self, client_factory, account_type, frontend):
        """Note: This test is to protect against an error caused by trying to
        invite users who have already been invited by not accepted
        https://itoworld.atlassian.net/browse/BODP-3025
        https://itoworld.atlassian.net/browse/BODP-3060
        """
        oldendays = datetime.now() - timedelta(days=4)
        client = client_factory(host=self.host)
        old_org = OrganisationFactory.create()
        new_org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(new_org,)
        )
        old_invite = InvitationFactory.create(
            email="existing_user@example.com",
            organisation=old_org,
            sent=oldendays,
            account_type=account_type,
        )
        client.force_login(user=admin)
        response = client.post(
            self.url,
            data={
                "email": "existing_user@example.com",
                "selected_item": frontend,
                "account_type": AccountType.developer.value,
            },
        )

        fished_out_invite = Invitation.objects.get(id=old_invite.id)
        assert response.status_code == 302
        assert fished_out_invite.organisation == new_org, "now using new organisation"
        assert fished_out_invite.sent.day == datetime.now().day, "sent out today"
        assert fished_out_invite.inviter == admin

    def test_inviting_an_agent_already_accepted_at_organisation(self, client_factory):
        """
        This is to protect against seeing multiple invites for the same agent in the
        frontend
        https://itoworld.atlassian.net/browse/BODP-3089
        """

        client = client_factory(host=self.host)
        orgs = OrganisationFactory.create_batch(5)
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=orgs[:1]
        )
        our_hero = UserFactory.create(
            account_type=AccountType.agent_user.value,
            organisations=orgs,
            email="existing_agent@agentsRus.com",
        )
        client.force_login(user=admin)

        response = client.post(
            self.url,
            data={
                "email": our_hero.email,
                "selected_item": "agent",
                "account_type": AccountType.developer.value,
            },
        )

        assert response.status_code == 200
        assert (
            response.context_data["form"].errors["email"][0]
            == "This agent is already active for this organisation"
        )

    def test_inviting_an_agent_multiple_times_only_creates_one_invite(
        self, client_factory
    ):
        """
        This is to protect against seeing multiple invites for the same agent in the
        frontend. The focus now being on multiple pending invites
        https://itoworld.atlassian.net/browse/BODP-3089
        """

        client = client_factory(host=self.host)
        org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        our_hero = UserFactory.create(
            account_type=AccountType.agent_user.value,
            email="existing_agent@agentsRus.com",
        )
        client.force_login(user=admin)

        for _ in range(3):
            response = client.post(
                self.url,
                data={
                    "email": our_hero.email,
                    "selected_item": "agent",
                    "account_type": AccountType.developer.value,
                },
            )

            assert response.status_code == 302
            AgentUserInvite.objects.get(organisation=org, agent=our_hero)

    def test_two_users_add_same_email(self, client_factory):
        """
        This is to protect against integrity errors when two users try and add the same
        email as an agent
        https://itoworld.atlassian.net/browse/BODP-4360
        """
        new_user_email = "new_user@test.test"
        org1, org2 = OrganisationFactory.create_batch(2)
        admin_1 = UserFactory(
            account_type=AccountType.org_admin.value, organisations=(org1,)
        )
        admin_2 = UserFactory(
            account_type=AccountType.org_admin.value, organisations=(org2,)
        )
        invite = InvitationFactory(
            email=new_user_email,
            organisation=org1,
            account_type=AgentUserType,
            inviter=admin_1,
        )
        AgentUserInviteFactory(
            agent=None,
            invitation=invite,
            organisation=org1,
            inviter=admin_1,
        )

        client = client_factory(host=self.host)
        client.force_login(user=admin_2)

        response = client.post(
            self.url,
            data={
                "email": new_user_email,
                "selected_item": "agent",
                "account_type": AgentUserType,
            },
        )

        assert response.status_code == 302
        old_key = invite.key
        invite.refresh_from_db()
        assert invite.organisation == org2, "existing invite org has been updated"
        assert invite.inviter == admin_2, "existing invite inviter has been updated"
        assert invite.agent_user_invite.inviter == admin_2
        assert invite.agent_user_invite.organisation == org2
        assert old_key != invite.key, "Check old invite is no longer valid"
