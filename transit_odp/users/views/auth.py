import logging

import allauth.account.views
import allauth.app_settings
from allauth.account import app_settings, signals
from allauth.account.adapter import get_adapter
from allauth.account.utils import perform_login
from allauth.utils import get_form_class
from django.contrib import messages
from django.contrib.auth.admin import sensitive_post_parameters_m
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import set_urlconf
from django.views.generic import TemplateView
from django_hosts.resolvers import reverse

from transit_odp.common.adapters import AccountAdapter

logger = logging.getLogger(__name__)


class SignupViewBase(allauth.account.views.SignupView):
    def has_invitation_started(self):
        """Check whether invitation has already started and reset state if it has

        Prevents invitated users calling GET on signup view more than once.
        """
        if self.is_invitation_mode and self.invitation_started:
            # unstash the verified email - this happens before 'has_permission' is
            # called, which means InviteOnlySignupView will immediately block the user.
            # Forcing the user to restart the flow
            self.adapter.unstash_account_verified_email(self.request)
            self.adapter.unstash_invitation_started(self.request)
            return True
        return False

    def get(self, request, *args, **kwargs):
        if self.is_invitation_mode:
            # Flag invitation started
            self.adapter.stash_invitation_started(self.request)
        return super().get(request, *args, **kwargs)

    def get_form_class(self):
        if not self.is_invitation_mode:
            form_id = "developer_signup"
        elif self.is_agent_invite:
            form_id = "agent_signup"
        else:
            form_id = "operator_signup"
        return get_form_class(app_settings.FORMS, form_id, self.form_class)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        email_field = form.fields["email"]
        if email_field.initial:
            # If email field is prepopulated (i.e. by invitation), disable field from
            # being edited
            email_field.widget.attrs.update({"readonly": True})
        return context

    @property
    def is_invitation_mode(self) -> bool:
        """Whether the sign up flow is for an invited user"""
        return self.adapter.stash_contains_account_verified_email(self.request)

    @property
    def is_agent_invite(self) -> bool:
        """Whether the invited user has an agent invite"""
        invite = self.adapter.invitation
        if invite is None:
            return False
        return invite.is_agent_user

    @property
    def invitation_started(self) -> bool:
        """Whether the initial signup page GET response has been returned"""
        return self.adapter.stash_contains_invitation_started(self.request)

    @property
    def adapter(self) -> AccountAdapter:
        return get_adapter(self.request)


class SignupView(SignupViewBase):
    @sensitive_post_parameters_m
    def dispatch(self, request, *args, **kwargs):
        # Check to see if invitation has already started
        if request.method == "GET":
            self.has_invitation_started()
        return super().dispatch(request, *args, **kwargs)


class InviteOnlySignupView(PermissionRequiredMixin, SignupViewBase):
    """Signup view which only shows signup form if user has come from invitation flow"""

    @sensitive_post_parameters_m
    def dispatch(self, request, *args, **kwargs):
        # We need this to run before PermissionRequiredMixin, which has its own dispatch
        # to call has_permission. Therefore, InviteOnlySignupView duplicate this code
        if request.method == "GET":
            self.has_invitation_started()
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self):
        # account_verified_email is stashed by invitations.views.AcceptInvite when the
        # user clicks the invitation link. the user is then redirected to the sign up
        # page. We also allow POST requests, bit of a hack, since the stash is cleared
        # after rendering the page, but is also needed to authorise the POST ac
        return self.is_invitation_mode

    def handle_no_permission(self):
        return self.render_invite_only()

    def render_invite_only(self):
        response_kwargs = {
            "request": self.request,
            "template": "account/signup_invite_only.html",
        }
        return self.response_class(**response_kwargs)


class LoginView(allauth.account.views.LoginView):
    def get_context_data(self, **kwargs):
        # Base class uses Django reverse so problematic with multi-tenancy,
        # Use set_urlconf for current thread
        # TODO - not sure of the consequences of this, does it need to be unset?
        set_urlconf(self.request.host.urlconf)

        context = super().get_context_data(**kwargs)

        # Retrieve stashed verified_email from session. This is set in ConfirmEmailView
        verified_email = get_adapter(self.request).unstash_verified_email(self.request)
        context["verified_email"] = verified_email
        if verified_email:
            # initialise the email field with the verified email
            form = context["form"]
            form.fields["login"].initial = verified_email
        return context


class LogoutSuccessView(TemplateView):
    template_name = "account/logout_success.html"


class ConfirmEmailView(allauth.account.views.ConfirmEmailView):
    def get_redirect_url(self):
        confirmation = self.object
        if confirmation and confirmation.email_address.verified:
            # Stash the verified email so we can display a message on the login page
            get_adapter(self.request).stash_verified_email(
                self.request, confirmation.email_address.email
            )
        return super().get_redirect_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Set the context to show if user is already verified
        context["verified"] = self.object and self.object.email_address.verified

        return context


class EmailVerificationSentView(
    UserPassesTestMixin, allauth.account.views.EmailVerificationSentView
):
    # prevent 'next=/account/confirm-email/' being added to url after redirecting away
    redirect_field_name = None

    def test_func(self):
        """Restricts user access to view"""
        return get_adapter(self.request).stash_contains_verification_email(self.request)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse("users:home", host=self.request.host.name)
            )
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Retrieve stashed verification_email from session.
        # This is set by 'respond_email_verification_sent' in adapter
        verification_email = get_adapter(self.request).unstash_verification_email(
            self.request
        )
        context["verification_email"] = verification_email
        return context


class PasswordResetView(allauth.account.views.PasswordResetView):
    def form_valid(self, form):
        # stash email of user
        email = form.cleaned_data["email"]
        get_adapter(self.request).stash_password_reset_email(self.request, email)
        return super().form_valid(form)


class PasswordResetDoneView(allauth.account.views.PasswordResetDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # retrieve stashed email
        email = get_adapter(self.request).unstash_password_reset_email(self.request)
        if email is None:
            logger.error("No password_reset_email was found in stash")
        context["password_reset_email"] = email
        return context


class PasswordResetFromKeyView(allauth.account.views.PasswordResetFromKeyView):
    # Overriding this view to pass redirect_url into perform_login, so the user is
    # taken to the confirmation page rather than the default LOGIN_REDIRECT_URL

    def form_valid(self, form):
        form.save()
        get_adapter(self.request).add_message(
            self.request, messages.SUCCESS, "account/messages/password_changed.txt"
        )
        signals.password_reset.send(
            sender=self.reset_user.__class__, request=self.request, user=self.reset_user
        )

        if app_settings.LOGIN_ON_PASSWORD_RESET:
            return perform_login(
                self.request,
                self.reset_user,
                redirect_url=self.success_url,
                email_verification=app_settings.EMAIL_VERIFICATION,
            )

        return super(PasswordResetFromKeyView, self).form_valid(form)
