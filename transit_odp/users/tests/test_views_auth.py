import pytest
from allauth.account.adapter import get_adapter
from allauth.account.forms import EmailAwarePasswordResetTokenGenerator
from allauth.account.models import EmailAddress, EmailConfirmation
from allauth.account.utils import user_pk_to_url_str
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import set_urlconf
from django.utils.timezone import now
from django_hosts.resolvers import get_host, reverse, reverse_host

import config.hosts
from transit_odp.common.adapters import AccountAdapter
from transit_odp.common.tests.utils import (
    add_message_middleware,
    add_session_middleware,
)
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.organisation.models import Organisation
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserInviteFactory,
    InvitationFactory,
    UserFactory,
)
from transit_odp.users.forms.auth import (
    AgentSignupForm,
    DeveloperSignupForm,
    OperatorSignupForm,
)
from transit_odp.users.models import AgentUserInvite, User
from transit_odp.users.views.auth import (
    EmailVerificationSentView,
    InviteOnlySignupView,
    LoginView,
    SignupView,
)

from allauth.core import context
from django.conf import settings
from django.contrib.sites.models import Site
from django.test import override_settings

pytestmark = pytest.mark.django_db


class TestViewsAuthBase:
    host = config.hosts.PUBLISH_HOST
    http_host = f"{settings.PUBLISH_SUBDOMAIN}.{settings.PARENT_HOST}"

    def setup_request(self, request_factory, invite_kwargs):
        url = reverse("account_signup", host=self.host)
        invite = InvitationFactory(**invite_kwargs)
        if invite.account_type != AccountType.developer.value:
            # Developers do not have invites
            invite.save()

        # Craft POST data
        data = {
            "email": invite.email,
            "password1": "a very long and complicated phrase",
            "password2": "a very long and complicated phrase",
            "first_name": "first",
            "last_name": "last",
            "opt_in_user_research": True,
            "share_app_usage": True,
        }

        if invite.account_type == AccountType.agent_user.value:
            data["agent_organisation"] = "agent_organisation"
            AgentUserInviteFactory.create(
                invitation=invite,
                agent=None,
                organisation=invite.organisation,
                inviter=invite.inviter,
            )

        elif invite.account_type == AccountType.developer.value:
            data["dev_organisation"] = "dev_organisation"
            data["description"] = "description"
            data["intended_use"] = 1
            data["national_interest"] = False
            data["regional_areas"] = "Here and there"

        request = request_factory.post(url, data=data)

        # simulate anonymous user
        request.user = AnonymousUser()
        request.host = self.host
        request.site = Site.objects.get(id=settings.ROOT_SITE_ID)

        # add session and message middleware
        request = add_session_middleware(request)
        request = add_message_middleware(request)

        if invite.account_type != AccountType.developer.value:
            # Developers dont have invites, never click on the accept-invite link
            # and never get their email address stashed in the session.
            # Instead they sign up and get an email confirmation email
            adapter: AccountAdapter = get_adapter(request)
            adapter.stash_verified_email(request, invite.email)

        return request, invite


class TestSignupView(TestViewsAuthBase):
    # TODO - add tests for signup view in every host

    def test_form_email_readonly_for_account_verified_email(
        self, settings, rf: RequestFactory
    ):
        """Tests the view returns a form with email field marked readonly when
        account_verified_email session variable is set. This is used by the invitation
        system."""
        host = get_host(self.host)
        url = reverse("account_signup", host=config.hosts.PUBLISH_HOST)

        settings.DEFAULT_HOST = config.hosts.DATA_HOST
        set_urlconf(host.urlconf)  # this normally handled by HostsRequestMiddleware

        email = "inviteduser@example.com"
        InvitationFactory.create(email=email)
        request = rf.get(url)

        # simulate anonymous user
        request.user = AnonymousUser()
        request.host = self.host

        # add session middleware
        request = add_session_middleware(request)

        # stash account_verified_email
        adapter = get_adapter(request)
        adapter.stash_verified_email(request, email)

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = SignupView.as_view()(request)

        # Assert
        assert response.status_code == 200
        assert "account/signup.html" in response.template_name

        form = response.context_data["form"]
        email_field = form.fields["email"]
        assert email_field.initial == email
        assert email_field.widget.attrs["readonly"] is True

    def test_invite_mode_blocks_after_initial_get(self, rf: RequestFactory):
        """Tests the view resets invitation_mode if user refreshes the page"""
        # Set up
        # Set DEFAULT_HOST to data service
        url = reverse("account_signup", host=config.hosts.PUBLISH_HOST)
        host = get_host(self.host)
        settings.DEFAULT_HOST = config.hosts.DATA_HOST
        set_urlconf(host.urlconf)  # this normally handled by HostsRequestMiddleware

        email = "inviteduser@example.com"
        InvitationFactory.create(email=email)
        request = rf.get(url)

        # simulate anonymous user
        request.user = AnonymousUser()
        request.host = self.host

        # add session middleware
        request = add_session_middleware(request)

        # stash account_verified_email
        adapter: AccountAdapter = get_adapter(request)
        adapter.stash_verified_email(request, email)

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            SignupView.as_view()(request)
            assert adapter.stash_contains_invitation_started(request)

            # Make second GET request
            SignupView.as_view()(request)

            # Assert
            assert not adapter.stash_contains_invitation_started(request)
            assert not adapter.stash_contains_account_verified_email(request)

    def test_user_settings_set_when_signs_up(self, client_factory):
        client = client_factory(host=config.hosts.DATA_HOST)
        url = reverse("account_signup", host=config.hosts.DATA_HOST)

        # Test
        email = "test@test.com"
        first_name = "first"
        last_name = "last"
        dev_organisation = "TestOrganisation"
        description = "description"
        response = client.post(
            url,
            data={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "password1": "a very long and complicated phrase",
                "password2": "a very long and complicated phrase",
                "account_type": "false",
                "opt_in_user_research": True,
                "share_app_usage": True,
                "dev_organisation": dev_organisation,
                "description": description,
                "intended_use": 1,
                "national_interest": False,
                "regional_areas": "Here and there",
            },
        )

        # Assert
        # On success, user is redirected. If response is 200,
        # validation errors have been added to the page
        assert response.status_code == 302
        user = get_user_model().objects.get(email=email)
        assert user.settings.opt_in_user_research is True
        assert user.settings.share_app_usage is True
        assert user.first_name == first_name
        assert user.last_name == last_name
        assert user.dev_organisation == dev_organisation
        assert user.description == description

    def test_character_limit_on_description(self, client_factory):
        client = client_factory(host=config.hosts.DATA_HOST)
        url = reverse("account_signup", host=config.hosts.DATA_HOST)

        # Test
        email = "test@test.com"
        first_name = "first"
        last_name = "last"
        dev_organisation = "TestOrganisation"
        description = "d" * 401
        response = client.post(
            url,
            data={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "password1": "a very long and complicated phrase",
                "password2": "a very long and complicated phrase",
                "account_type": "false",
                "opt_in_user_research": True,
                "share_app_usage": True,
                "dev_organisation": dev_organisation,
                "description": description,
            },
        )

        assert response.status_code == 200
        assert (
            response.context["form"].errors["description"][0]
            == "Ensure this value has at most 400 characters (it has 401)."
        )

    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_new_user_has_same_entries_as_invitation(self, mailoutbox, request_factory):
        org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        admin.settings.notify_invitation_accepted = True
        admin.settings.save()
        user_email = "newuser@test.test"
        request, invite = self.setup_request(
            request_factory,
            {
                "account_type": AccountType.org_staff.value,
                "email": user_email,
                "inviter": admin,
                "organisation": org,
            },
        )

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            SignupView.as_view()(request)
        fished_out_user = User.objects.get(email=user_email)

        assert fished_out_user.email == invite.email
        assert fished_out_user.account_type == invite.account_type
        assert fished_out_user.organisation == invite.organisation

    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_new_agent_signs_up(self, mailoutbox, request_factory):
        org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        admin.settings.notify_invitation_accepted = True
        admin.settings.save()
        user_email = "newagent@test.test"
        request, invite = self.setup_request(
            request_factory,
            {
                "account_type": AccountType.agent_user.value,
                "email": user_email,
                "inviter": admin,
                "organisation": org,
            },
        )
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            SignupView.as_view()(request)
        fished_out_user = User.objects.get(email=user_email)
        fished_out_agent_invitation = AgentUserInvite.objects.get(invitation=invite)

        assert fished_out_user.email == invite.email
        assert fished_out_user.account_type == invite.account_type
        assert fished_out_user.organisation == invite.organisation
        assert fished_out_agent_invitation.status == AgentUserInvite.ACCEPTED
        assert fished_out_user.agent_organisation == "agent_organisation"
        assert fished_out_user.settings.opt_in_user_research is True

    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_key_contact_is_added_when_signs_up(self, request_factory: RequestFactory):
        # Set up
        request, invite = self.setup_request(
            request_factory,
            {"account_type": AccountType.org_admin.value, "is_key_contact": True},
        )

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = SignupView.as_view()(request)
        organisation = Organisation.objects.get(id=invite.organisation.id)

        assert response.status_code == 302
        assert organisation.key_contact.email == invite.email

    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_organisation_is_active_when_signs_up(
        self, request_factory: RequestFactory
    ):
        # Set up
        request, invite = self.setup_request(
            request_factory,
            {"account_type": AccountType.org_admin.value, "is_key_contact": True},
        )
        # set organisation's is_active to False initially
        invite.organisation.is_active = False
        invite.organisation.save()

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = SignupView.as_view()(request)
        organisation = Organisation.objects.get(id=invite.organisation.id)

        assert response.status_code == 302
        assert (
            organisation.is_active is True
        )  # organisation set to 'is_active=True' once invite is accepted

    @pytest.mark.parametrize(
        ("account_type", "is_key_contact"),
        (
            (AccountType.org_admin.value, False),
            (AccountType.org_staff.value, False),
        ),
        ids=["Org Admin", "Org Staff"],
    )
    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_key_contact_is_none_when_non_key_contact_signs_up(
        self, request_factory: RequestFactory, account_type, is_key_contact
    ):
        # Set up
        request, invite = self.setup_request(
            request_factory,
            {"account_type": account_type, "is_key_contact": is_key_contact},
        )

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = SignupView.as_view()(request)
        organisation = Organisation.objects.get(id=invite.organisation.id)

        assert response.status_code == 302
        assert organisation.key_contact is None
    
    def test_developer_sign_up_form(self, request_factory):
        self.host = config.hosts.DATA_HOST
        request, invite = self.setup_request(
            request_factory, {"account_type": AccountType.developer.value}
        )

        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = SignupView.as_view()(request)
        User.objects.get(email=invite.email)

        assert response.status_code == 302
        self.host = config.hosts.PUBLISH_HOST

    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_second_user_accepts_first(self, request_factory: RequestFactory):
        """
        This test simulates the conditions needed for this bug.
        https://itoworld.atlassian.net/browse/BODP-2578
        The issue occurs when you have a key contact that does not
        accept the invite and another user accepts instead. The organisation
        never gets set to active.
        """
        host = config.hosts.PUBLISH_HOST
        url = reverse("account_signup", host=host)

        superadmin = UserFactory.create(account_type=AccountType.site_admin.value)
        org = OrganisationFactory.create(
            short_name="This Organisation", is_active=False
        )
        InvitationFactory.create(
            email="ignorer@test.test",
            is_key_contact=True,
            organisation=org,
            account_type=AccountType.org_admin.value,
            inviter=superadmin,
        )
        this_guys_invite = InvitationFactory.create(
            email="accepter@test.test",
            is_key_contact=False,
            organisation=org,
            account_type=AccountType.org_admin.value,
            inviter=superadmin,
        )

        # Craft POST data
        data = {
            "email": this_guys_invite.email,
            "password1": "a very long and complicated phrase",
            "password2": "a very long and complicated phrase",
            "first_name": "Accepter",
            "last_name": "Ontheball",
            "opt_in_user_research": True,
            "share_app_usage": True,
        }
        request = request_factory.post(url, data=data)

        # simulate anonymous user
        request.user = AnonymousUser()
        request.host = host

        # add session and message middleware
        request = add_session_middleware(request)
        request = add_message_middleware(request)

        # stash account_verified_email
        adapter: AccountAdapter = get_adapter(request)
        adapter.stash_verified_email(request, this_guys_invite.email)

        # Test
        request.META['HTTP_HOST'] = self.http_host
        request.site = Site.objects.get(id=settings.ROOT_SITE_ID)
        with context.request_context(request):
            response = SignupView.as_view()(request)
        org_from_database = Organisation.objects.get(id=org.id)

        assert response.status_code == 302
        assert (
            org_from_database.is_active is True
        ), "organisation set to 'is_active=True' once invite is accepted"

        assert (
            org_from_database.key_contact is None
        ), "key contact user has ignored the email so none set"

    def test_developers_get_correct_form(self, settings, rf: RequestFactory):
        host = get_host(config.hosts.DATA_HOST)
        url = reverse("account_signup", host=config.hosts.DATA_HOST)

        settings.DEFAULT_HOST = config.hosts.DATA_HOST
        set_urlconf(host.urlconf)  # this normally handled by HostsRequestMiddleware

        request = rf.get(url)

        # simulate anonymous user
        request.user = AnonymousUser()
        request.host = config.hosts.DATA_HOST

        # add session middleware
        request = add_session_middleware(request)
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = SignupView.as_view()(request)
            assert isinstance(response.context_data["form"], DeveloperSignupForm)

    @pytest.mark.parametrize(
        ("account_type", "email", "form"),
        [
            (AccountType.org_staff.value, "staff@example.com", OperatorSignupForm),
            (AccountType.org_admin.value, "admin@example.com", OperatorSignupForm),
            (AccountType.agent_user.value, "agent@example.com", AgentSignupForm),
        ],
    )
    def test_org_users_get_correct_signup_form(
        self, email, account_type, form, rf: RequestFactory
    ):
        host = get_host(self.host)
        url = reverse("account_signup", host=config.hosts.PUBLISH_HOST)

        set_urlconf(host.urlconf)  # this normally handled by HostsRequestMiddleware

        InvitationFactory.create(email=email, account_type=account_type)
        request = rf.get(url)

        # simulate anonymous user
        request.user = AnonymousUser()
        request.host = self.host

        # add session middleware
        request = add_session_middleware(request)

        # stash account_verified_email
        adapter = get_adapter(request)
        adapter.stash_verified_email(request, email)

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = SignupView.as_view()(request)

        assert isinstance(response.context_data["form"], form)


class TestInviteOnlySignupView(TestViewsAuthBase):
    def test_has_permission(self, rf: RequestFactory):
        # Set up
        # Set DEFAULT_HOST to publish service
        host = get_host(self.host)
        settings.DEFAULT_HOST = config.hosts.PUBLISH_HOST
        set_urlconf(host.urlconf)  # this normally handled by HostsRequestMiddleware

        request = rf.get("/fake-url")
        request.user = AnonymousUser()
        request = add_session_middleware(request)

        email = "invited@org.com"
        InvitationFactory.create(email=email)
        adapter = get_adapter(request)
        adapter.stash_verified_email(request, email)

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            response = InviteOnlySignupView.as_view()(request)

        # Assert
        assert response.status_code == 200
        assert "account/signup.html" in response.template_name

    def test_no_permission(self, rf: RequestFactory, mocker):
        # Set up
        # Set DEFAULT_HOST to publish service
        host = get_host(self.host)
        settings.DEFAULT_HOST = config.hosts.PUBLISH_HOST
        set_urlconf(host.urlconf)  # this normally handled by HostsRequestMiddleware

        request = rf.get("/fake-url")
        request.host = self.host
        request = add_session_middleware(request)

        request.user = AnonymousUser()

        mocked_site = mocker.Mock()
        mocked_site.name = "Publish Data Service"
        request.site = mocked_site

        # Test
        response = InviteOnlySignupView.as_view()(request)

        # Assert
        assert response.status_code == 200
        assert "account/signup_invite_only.html" in response.template_name


class TestLoginView(TestViewsAuthBase):
    host = config.hosts.DATA_HOST
    url = reverse("account_login", host=config.hosts.DATA_HOST)

    def test_login_form_initialised_with_verified_email(self, rf: RequestFactory):
        """Test the email form input is initialised with email when the session
        contains stashed account_verified_email"""
        # Set up
        email = "confirmeduser@example.com"

        hostname = reverse_host(self.host)
        request = rf.get(self.url, SERVER_NAME=hostname)
        request.host = get_host(self.host)

        # simulate anonymous user
        request.user = AnonymousUser()

        # add session middleware
        request = add_session_middleware(request)

        # stash account_verified_email
        adapter = get_adapter(request)
        adapter.stash_verified_email(request, email)

        # Test
        with context.request_context(request):
            response = LoginView.as_view()(request)

        # Assert
        assert response.status_code == 200
        assert "account/login.html" in response.template_name

        form = response.context_data["form"]
        field = form.fields["login"]
        assert field.initial == email


class TestConfirmEmailView(TestViewsAuthBase):
    host = config.hosts.DATA_HOST
    signin_url = reverse("account_login", host=config.hosts.DATA_HOST)

    def test_account_verified_email_set_on_confirm(self, user_factory, client_factory):
        """Tests the user is redirected, on POST, to the login page and
        account_verified_email is set in the session"""
        # Set up
        client = client_factory(host=self.host)
        email = "unverifieduser@example.com"
        user = user_factory(email=email, verified=False)
        emailaddress = EmailAddress.objects.create(
            user=user, email=email, verified=False, primary=True
        )

        # confirmation = EmailConfirmationHMAC(emailaddress)
        # no longer using HMAC to generate emails
        confirmation = EmailConfirmation.create(emailaddress)
        confirmation.sent = now()
        confirmation.save()

        url = reverse("account_confirm_email", host=self.host, args=[confirmation.key])

        # Test
        response = client.post(url)

        # Assert
        assert response.status_code == 302
        # assert response.url == self.signin_url
        assert client.session.get("account_verified_email") == email


class TestEmailVerificationSentView(TestViewsAuthBase):
    host = config.hosts.DATA_HOST
    url = reverse("account_email_verification_sent", host=config.hosts.DATA_HOST)
    signin_url = reverse("account_login", host=config.hosts.DATA_HOST)
    my_account_url = reverse("users:home", host=config.hosts.DATA_HOST)

    def test_verification_stashed_email(self, rf: RequestFactory):
        """Test the verification sent page displays when the session contains
        the stashed verification_email (set via all_auth.account.utils.perform_login)"""
        # Set up
        email = "signedupuser@example.com"
        request = rf.get(self.url)

        # add session middleware
        request = add_session_middleware(request)

        # stash verification_email
        adapter = get_adapter(request)
        adapter.stash_verification_email(request, email)

        # Test
        response = EmailVerificationSentView.as_view()(request)

        # Assert
        assert response.status_code == 200
        assert "account/verification_sent.html" in response.template_name
        assert response.context_data["verification_email"] == email

    @pytest.mark.parametrize(
        "user_is_logged_in,redirect_url", [(True, my_account_url), (False, signin_url)]
    )
    def test_redirects_if_no_stashed_email_for_logged_in_user(
        self,
        user_is_logged_in: bool,
        redirect_url: str,
        user: settings.AUTH_USER_MODEL,
        client_factory,
    ):
        """Tests the view is not accessible to normal requests (only accessed via
        redirect with session state Tests logged in users are redirected to
        MyAccountView and unauth users to the signin page."""

        client = client_factory(host=self.host)
        if user_is_logged_in:
            client.force_login(user=user)

        response = client.get(self.url)

        assert response.status_code == 302


class TestPasswordReset(TestViewsAuthBase):
    host = config.hosts.DATA_HOST

    def test_reset_done_page_context(self, user_factory, client_factory):
        """Tests context of confirmation page after user requests password reset.

        The context should contain the email of the account requesting password reset
        """
        # Set up
        client = client_factory(host=self.host)

        # create user
        email = "forgottenpassworduser@example.com"
        user_factory(email=email)

        # password reset request page
        url = reverse("account_reset_password", host=self.host)

        # Test
        # post email address
        response = client.post(url, data={"email": email}, follow=True)

        # Assert
        assert response.status_code == 200
        assert "account/password_reset_done.html" in response.template_name
        assert response.context["password_reset_email"] == email

    def test_reset_done_page_for_invalid_email(self, user_factory, client_factory):
        """Tests context of confirmation page after user requests password reset,
        when the user email is not already registered
        Done as part of BODP-1963

        The context should contain the email of the account requesting password reset
        """
        # Set up
        client = client_factory(host=self.host)

        # create user
        email = "forgottenpassworduser@example.com"
        # Do not add the email to existing user list
        # user = user_factory(email=email)

        # password reset request page
        url = reverse("account_reset_password", host=self.host)

        # Test
        # post email address
        response = client.post(url, data={"email": email}, follow=True)

        # Assert
        assert response.status_code == 200
        assert "account/password_reset_done.html" in response.template_name
        assert response.context["password_reset_email"] == email


class TestPasswordResetFromKeyView(TestViewsAuthBase):
    host = config.hosts.DATA_HOST

    def test_redirects_to_confirmation_page_on_success(
        self, user_factory, client_factory
    ):
        """Tests user is redirected to 'done' page after changing password through the
        password reset flow. The default behaviour was to redirect back to login page
        without any visual confirmation.
        """
        # Set up
        client = client_factory(host=self.host)
        # create user
        email = "forgottenpassworduser@example.com"
        user = user_factory(email=email)

        # generate password reset link
        token_generator = EmailAwarePasswordResetTokenGenerator()
        key = token_generator.make_token(user)
        url = reverse(
            "account_reset_password_from_key",
            kwargs=dict(uidb36=user_pk_to_url_str(user), key=key),
            host=self.host,
        )

        # Test
        new_password = "fsfsw52542g34U"
        response = client.get(url)  # does some redirecting and sets session variables

        # post new password
        response = client.post(
            response.url, data={"password1": new_password, "password2": new_password}
        )

        # Assert
        assert response.status_code == 302
        # assert response.url == reverse('account_reset_password_from_key_done',
        # host=config.hosts.DATA_HOST)



class TestNotifications(TestViewsAuthBase):
    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_inviter_notification(self, mailoutbox, request_factory):
        org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        admin.settings.notify_invitation_accepted = True
        admin.settings.save()
        user_email = "newuser@test.test"
        request, invite = self.setup_request(
            request_factory,
            {
                "account_type": AccountType.org_staff.value,
                "email": user_email,
                "inviter": admin,
                "organisation": org,
            },
        )

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            SignupView.as_view()(request)

        assert mailoutbox[-1].subject == "Your team member has accepted your invitation"

    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_new_agent_accepted_notifications(self, mailoutbox, request_factory):
        """Tests both agent and organisation receive an email notification"""
        org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        admin.settings.notify_invitation_accepted = True
        admin.settings.save()
        user_email = "newagent@test.test"
        request, invite = self.setup_request(
            request_factory,
            {
                "account_type": AccountType.agent_user.value,
                "email": user_email,
                "inviter": admin,
                "organisation": org,
            },
        )

        # Test
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            SignupView.as_view()(request)

        assert len(mailoutbox) == 2
        mailoutbox.sort(key=lambda mail: mail.subject)
        first, second = mailoutbox
        assert first.subject == "Agent agent_organisation has accepted your invitation"
        assert (
            second.subject
            == f"You have accepted the request to be an agent on behalf of "
            f"{org.name}"
        )

    @override_settings(LOGIN_REDIRECT_URL="/accounts/profile/")
    def test_muted_inviter_doesnt_trigger_notification(
        self, mailoutbox, request_factory
    ):
        org = OrganisationFactory.create()
        admin = UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        user_email = "newuser@test.test"
        request, invite = self.setup_request(
            request_factory,
            {
                "account_type": AccountType.org_staff.value,
                "email": user_email,
                "inviter": admin,
                "organisation": org,
            },
        )
        request.META['HTTP_HOST'] = self.http_host
        with context.request_context(request):
            SignupView.as_view()(request)

        assert not mailoutbox
