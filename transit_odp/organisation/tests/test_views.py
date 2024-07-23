import pytest
from allauth.account.adapter import get_adapter
from django_hosts.resolvers import get_host, reverse

import config.hosts
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.tests.utils import add_session_middleware
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.organisation.forms.management import (
    Invitation,
    InvitationSubsequentForm,
    UserEditForm,
)
from transit_odp.organisation.views import (
    InviteView,
    ManageView,
    ResendInviteView,
    UserEditView,
    UserIsActiveView,
)
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserInviteFactory,
    InvitationFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.views.mixins import OrgAdminViewMixin

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestManageView:
    host = config.hosts.PUBLISH_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminOrOrgAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(ManageView, OrgAdminViewMixin)

    def test_correct_template_used(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        url = reverse(
            "users:manage",
            kwargs={"pk": user.organisation.id},
            host=config.hosts.PUBLISH_HOST,
        )
        client.force_login(user=user)
        response = client.get(url)

        assert response.status_code == 200
        assert "users/users_manage.html" in [t.name for t in response.templates]

    def test_user_list(self, client_factory):
        """Test user list containing users and invited users is returned in the
        context"""
        organisation = OrganisationFactory()
        user = UserFactory(
            account_type=AccountType.org_admin.value, organisations=(organisation,)
        )
        InvitationFactory(
            account_type=AccountType.org_staff.value, organisation=organisation
        )
        AgentUserInviteFactory(status="pending", organisation=organisation)
        accepted_agent = AgentUserInviteFactory(
            status="active", organisation=organisation
        )
        accepted_agent.agent.organisations.add(organisation)
        url = reverse(
            "users:manage",
            kwargs={"pk": user.organisation.id},
            host=config.hosts.PUBLISH_HOST,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 200
        expected_users = organisation.users.all()
        expected_pending_standard_invites = organisation.invitation_set.filter(
            accepted=False
        )
        expected_pending_agent_invites = organisation.agentuserinvite_set.filter(
            status=AgentUserInvite.PENDING
        )

        pending_standard_invites = response.context["pending_standard_invites"]
        pending_agent_invites = response.context["pending_agent_invites"]
        users = response.context["users"]

        assert list(pending_standard_invites) == list(expected_pending_standard_invites)
        assert list(pending_agent_invites) == list(expected_pending_agent_invites)
        assert list(users) == list(expected_users)
        assert users.count() == 2
        assert pending_agent_invites.count() == 1
        assert pending_standard_invites.count() == 1

    def test_context(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        url = reverse(
            "users:manage",
            kwargs={"pk": user.organisation.id},
            host=config.hosts.PUBLISH_HOST,
        )
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["object"] == user.organisation
        assert response.context["user"] == user
        assert (
            len(response.context["users"]) == 1
        )  # this is tests more thoroughly in test_user_list


@pytest.mark.django_db
class TestInviteView:
    host = config.hosts.PUBLISH_HOST
    url = reverse("users:invite", host=config.hosts.PUBLISH_HOST)

    def test_view_permission_mixin(self):
        """Tests the view subclasses OrgAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(InviteView, OrgAdminViewMixin)

    def test_correct_template_used(self, client_factory):
        client = client_factory(host=self.host)
        user = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "users/users_invite.html" in [t.name for t in response.templates]

    def test_form_kwargs(self, request_factory):
        user = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        request = request_factory.get("fake-url/")
        request.user = user
        request.host = get_host(self.host)
        view = InviteView()
        view.request = request
        kwargs = view.get_form_kwargs()
        assert view.form_class == InvitationSubsequentForm
        assert "cancel_url" in kwargs
        assert (
            reverse(
                "users:manage",
                kwargs={"pk": user.organisation.id},
                host=config.hosts.PUBLISH_HOST,
            )
            in kwargs["cancel_url"]
        )

    def test_invitation_created(self, client_factory):
        # Set up
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)

        url = reverse("users:invite", host=self.host)

        # Test
        email = "test@test.com"
        response = client.post(
            url,
            data={
                "email": email,
                "selected_item": "staff",
                "account_type": AccountType.developer.value,
            },
        )

        # On success, user is redirected. If response is 200, validation errors have
        # been added to the page
        assert response.status_code == 302
        # No assert because .get() will throw error if number of returned
        # Invitations != 1
        invite = Invitation.objects.get(email=email)
        assert invite.is_key_contact is False
        assert invite.sent

    def test_send_invitation_on_success(self, client_factory, mailoutbox):
        """Tests form.send_invitation is called by form_valid"""
        # Set up
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)

        url = reverse("users:invite", host=self.host)

        # Test
        email = "test@test.com"
        response = client.post(
            url,
            data={
                "email": email,
                "selected_item": "staff",
                "account_type": AccountType.developer.value,
            },
        )

        # Assert
        assert mailoutbox[-1].subject == "You have been invited to publish bus data"
        assert response.status_code == 302

    def test_send_invitation_on_agent_success(self, client_factory, mailoutbox):
        """Tests new agent invitation is sent"""
        # Set up
        client = client_factory(host=self.host)
        org = OrganisationFactory()
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(org,),
        )
        client.force_login(user=admin)

        url = reverse("users:invite", host=self.host)

        # Test
        email = "test@test.com"
        response = client.post(
            url,
            data={
                "email": email,
                "selected_item": "agent",
                "account_type": AccountType.developer.value,
            },
        )

        # Assert
        assert (
            mailoutbox[-1].subject
            == f"{org.name} has invited you to act as an agent on behalf of them"
        )
        assert response.status_code == 302

    def test_stash_data(self, request_factory, mocker):
        """Tests data is stashed in session"""
        request = request_factory.get("fake-url/")
        request = add_session_middleware(request)

        view = InviteView()
        view.request = request

        # mock out form
        mocked_form = mocker.Mock()
        mocked_form.cleaned_data = {"email": "test@test.com"}

        adapter = get_adapter(request)

        # Test
        view.stash_data(mocked_form)

        # Assert
        assert adapter.stash_contains_invite_email(request)
        assert adapter.unstash_invite_email(request) == "test@test.com"


@pytest.mark.django_db
class TestResendInviteView:
    host = config.hosts.PUBLISH_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses OrgAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(InviteView, OrgAdminViewMixin)

    def test_correct_template_used(self, client_factory):
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)
        invited = InvitationFactory(
            account_type=AccountType.org_staff.value, organisation=admin.organisation
        )
        url = reverse("users:re-invite", args=[invited.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert "users/user_resend_invite.html" in [t.name for t in response.templates]

    def test_form_kwargs(self, request_factory):
        # Set up
        user = UserFactory(account_type=AccountType.org_admin.value)

        request = request_factory.get("fake-url/")
        request.user = user
        request.host = get_host(self.host)

        view = ResendInviteView()
        view.request = request

        # Test
        kwargs = view.get_form_kwargs()

        # Assert
        assert view.form_class == ConfirmationForm
        assert "cancel_url" in kwargs
        assert (
            reverse(
                "users:manage",
                kwargs={"pk": user.organisation.id},
                host=config.hosts.PUBLISH_HOST,
            )
            in kwargs["cancel_url"]
        )

    def test_send_invitation_on_success(self, mocker, request_factory):
        """Tests invitation.send_invitation is called on post"""
        # Set up
        view = ResendInviteView()

        # mock out invitation
        mocked_invitation = mocker.Mock(id=123)
        mocker.patch.object(view, "get_object", return_value=mocked_invitation)

        user = UserFactory(account_type=AccountType.org_admin.value)
        request = request_factory.get("fake-url/")
        request.user = user
        request.host = get_host(self.host)

        view.request = request

        # Test
        response = view.post(request)

        # Assert
        mocked_invitation.send_invitation.assert_called_once_with(request)
        assert response.status_code == 302
        assert response.url == reverse(
            "users:re-invite-success",
            kwargs={"pk": mocked_invitation.id},
            host=config.hosts.PUBLISH_HOST,
        )

    def test_queryset_filters_by_org(self, request_factory):
        user = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        invitations = InvitationFactory.create_batch(
            3, account_type=AccountType.org_staff.value, organisation=user.organisation
        )
        InvitationFactory.create_batch(
            3,
            account_type=AccountType.org_admin.value,
            organisation=OrganisationFactory(),
        )

        request = request_factory.get("fake-url/")
        request.user = user
        view = ResendInviteView()
        view.request = request
        qs = view.get_queryset()
        assert list(qs) == invitations


@pytest.mark.django_db
class TestResendInviteSuccessView:
    host = config.hosts.PUBLISH_HOST

    def test_correct_template_used(self, client_factory):
        # Set up
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)
        invited = InvitationFactory(
            account_type=AccountType.org_staff.value, organisation=admin.organisation
        )
        url = reverse("users:re-invite-success", args=[invited.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert "users/user_resend_invite_success.html" in [
            t.name for t in response.templates
        ]


@pytest.mark.django_db
class TestUserIsActiveView:
    host = config.hosts.PUBLISH_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses OrgAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(InviteView, OrgAdminViewMixin)

    def test_correct_template_used(self, client_factory):
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)
        staff = UserFactory(
            account_type=AccountType.org_staff.value,
            organisations=(admin.organisation,),
        )
        url = reverse("users:archive", args=[staff.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert "users/user_archive.html" in [t.name for t in response.templates]

    # TODO Fix this unit test to process get_form_kwargs()
    def test_form_kwargs(self, request_factory):
        user = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )

        request = request_factory.get("fake-url/")
        request.user = user
        request.host = get_host(self.host)

        view = UserIsActiveView()
        view.request = request
        view.kwargs = {"pk": user.id}
        kwargs = view.get_form_kwargs()
        assert view.form_class == ConfirmationForm
        assert "cancel_url" in kwargs
        assert (
            reverse(
                "users:manage-user-detail",
                kwargs={"pk": user.id},
                host=config.hosts.PUBLISH_HOST,
            )
            in kwargs["cancel_url"]
        )

    @pytest.mark.parametrize("is_active", [True, False])
    def test_user_archival(self, is_active, client_factory):
        """Tests active user is set to (in)active on post depending on their current
        is_active"""
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)
        staff = UserFactory(
            is_active=is_active,
            account_type=AccountType.org_staff.value,
            organisations=(admin.organisation,),
        )
        url = reverse("users:archive", args=[staff.id], host=self.host)
        response = client.post(url)
        staff.refresh_from_db()
        assert staff.is_active is not is_active
        assert response.status_code == 302

    def test_queryset_filters_by_org(self, request_factory):
        user = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        staff = UserFactory.create_batch(
            3,
            account_type=AccountType.org_staff.value,
            organisations=(user.organisation,),
        )
        UserFactory.create_batch(
            3,
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )

        request = request_factory.get("fake-url/")
        request.user = user

        view = UserIsActiveView()
        view.request = request
        qs = view.get_queryset()

        def ordered(seq):
            return sorted(seq, key=lambda obj: obj.id)

        assert ordered(qs) == ordered(staff)


@pytest.mark.django_db
class TestUserDetailView:
    host = config.hosts.PUBLISH_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses OrgAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(InviteView, OrgAdminViewMixin)

    def test_correct_template_used(self, client_factory):
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)

        staff = UserFactory(
            account_type=AccountType.org_staff.value,
            organisations=(admin.organisation,),
        )
        url = reverse("users:manage-user-detail", args=[staff.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert "users/users_manage_detail.html" in [t.name for t in response.templates]

    def test_cannot_access_detail_page_for_users_of_other_organisations(
        self, client_factory
    ):
        def get_response(user):
            url = reverse("users:manage-user-detail", args=[user.id], host=self.host)
            return client.get(url)

        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)

        staff = UserFactory.create_batch(
            3,
            account_type=AccountType.org_staff.value,
            organisations=(admin.organisation,),
        )

        other_users = UserFactory.create_batch(
            3,
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )

        for user in staff:
            response = get_response(user)
            assert response.status_code == 200

        for user in other_users:
            response = get_response(user)
            assert response.status_code == 404


@pytest.mark.django_db
class TestUserEditView:
    host = config.hosts.PUBLISH_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses OrgAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(InviteView, OrgAdminViewMixin)

    def test_correct_template_used(self, client_factory):
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)
        staff = UserFactory(
            account_type=AccountType.org_staff.value,
            organisations=(admin.organisation,),
        )
        url = reverse("users:manage-user-edit", args=[staff.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert "users/users_manage_edit.html" in [t.name for t in response.templates]

    def test_form_kwargs(self, request_factory):
        UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        staff = UserFactory(
            account_type=AccountType.org_staff.value,
            organisations=(OrganisationFactory(),),
        )
        url = reverse("users:manage-user-detail", args=[staff.id], host=self.host)
        request = request_factory.get("fake-url/")
        request.host = get_host(self.host)
        request.cancel_url = url

        view = UserEditView()
        view.request = request
        view.kwargs = {"pk": staff.id}

        kwargs = view.get_form_kwargs()
        assert view.form_class == UserEditForm
        assert "cancel_url" in kwargs
        assert kwargs["cancel_url"] == url

    def test_form_kwargs_with_admin(self, request_factory):
        # Set up
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        staff = UserFactory(
            account_type=AccountType.org_staff.value,
            organisations=(OrganisationFactory(),),
        )
        cancel_url = reverse(
            "users:manage-user-detail",
            kwargs={"pk": staff.id},
            host=config.hosts.PUBLISH_HOST,
        )

        request = request_factory.get("fake-url/")
        request.user = admin
        request.host = get_host(self.host)

        view = UserEditView()
        view.request = request
        view.kwargs = {"pk": staff.id}

        kwargs = view.get_form_kwargs()

        # Assert
        assert view.form_class == UserEditForm
        assert "cancel_url" in kwargs
        assert cancel_url in kwargs["cancel_url"]

    def test_cannot_access_edit_page_for_users_of_other_organisations(
        self, client_factory
    ):
        def get_response(user):
            url = reverse("users:manage-user-edit", args=[user.id], host=self.host)
            return client.get(url)

        # Set up
        client = client_factory(host=self.host)

        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)

        staff = UserFactory.create_batch(
            3,
            account_type=AccountType.org_staff.value,
            organisations=(admin.organisation,),
        )

        other_users = UserFactory.create_batch(
            3,
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )

        # Assert
        for user in staff:
            response = get_response(user)
            assert response.status_code == 200

        for user in other_users:
            response = get_response(user)
            assert response.status_code == 404

    def test_user_edits_get_stored_in_database(self, client_factory):
        client = client_factory(host=self.host)
        admin = UserFactory(
            account_type=AccountType.org_admin.value,
            organisations=(OrganisationFactory(),),
        )
        client.force_login(user=admin)
        staff = UserFactory(
            username="old_username",
            email="old_email@test.com",
            is_active=True,
            account_type=AccountType.org_staff.value,
            organisations=(admin.organisation,),
        )
        url = reverse("users:manage-user-edit", args=[staff.id], host=self.host)
        response = client.post(
            url,
            {
                "username": "new_username",
                "email": "new_email@test.com",
                "account_type": AccountType.org_admin.value,
            },
        )
        staff.refresh_from_db()
        assert staff.username == "new_username"
        assert staff.email == "new_email@test.com"
        assert staff.account_type == AccountType.org_admin.value
        assert response.status_code == 302


@pytest.mark.django_db
class TestAgentUserResponses:
    host = config.hosts.PUBLISH_HOST

    def setup_agent_invites(self, client_factory):
        orgs = OrganisationFactory.create_batch(3)
        agent = UserFactory.create(
            account_type=AccountType.agent_user.value,
            agent_organisation="agentsRus",
            organisations=orgs,
        )
        for org in orgs:
            AgentUserInviteFactory.create(
                agent=agent, organisation=org, status="accepted"
            )

        pending_invite = AgentUserInviteFactory.create(agent=agent)
        client = client_factory(host=self.host)
        client.force_login(user=agent)
        return client, pending_invite

    def test_agent_invite_accepted(self, client_factory, mailoutbox):
        client, invite = self.setup_agent_invites(client_factory)
        url = reverse("users:agent-user-response", args=[invite.id], host=self.host)
        response = client.post(url, {"status": "accepted"})

        assert response.status_code == 302
        fished_out_invite = AgentUserInvite.objects.get(id=invite.id)
        assert fished_out_invite.status == "accepted"
        assert fished_out_invite.organisation in list(
            fished_out_invite.agent.organisations.all()
        )
        assert len(mailoutbox) == 2
        mailoutbox.sort(key=lambda mail: mail.subject)
        first, second = mailoutbox
        assert first.subject == "Agent agentsRus has accepted your invitation"
        assert (
            second.subject
            == f"You have accepted the request to be an agent on behalf of "
            f"{invite.organisation.name}"
        )

    def test_agent_invite_rejected(self, client_factory, mailoutbox):
        client, invite = self.setup_agent_invites(client_factory)
        url = reverse("users:agent-user-response", args=[invite.id], host=self.host)
        response = client.post(url, {"status": "rejected"})

        assert response.status_code == 302
        fished_out_invite = AgentUserInvite.objects.get(id=invite.id)
        assert fished_out_invite.status == "rejected"
        assert fished_out_invite.organisation not in list(
            fished_out_invite.agent.organisations.all()
        )
        assert len(mailoutbox) == 2
        mailoutbox.sort(key=lambda mail: mail.subject)
        first, second = mailoutbox
        assert (
            first.subject
            == f"You have rejected the request to become an agent on behalf of "
            f"{invite.organisation.name}"
        )
        assert (
            second.subject == "agentsRus has rejected your request to act as an agent"
        )

    def test_agent_leaves_organisation(self, client_factory, mailoutbox):
        client, _ = self.setup_agent_invites(client_factory)
        first_active_invite = AgentUserInvite.objects.filter(status="accepted").first()
        url = reverse(
            "users:agent-user-leave", args=[first_active_invite.id], host=self.host
        )
        response = client.post(url, {"status": "inactive"})

        first_active_invite.refresh_from_db()
        assert response.status_code == 302
        assert first_active_invite.status == "inactive"
        assert first_active_invite.organisation not in list(
            first_active_invite.agent.organisations.all()
        )
        assert len(mailoutbox) == 2
        mailoutbox.sort(key=lambda mail: mail.subject)
        first, second = mailoutbox
        assert (
            first.subject == f"You have stopped acting as an agent on behalf of "
            f"{first_active_invite.organisation.name}"
        )
        assert second.subject == "agentsRus has terminated their role as an agent"
