from typing import Optional

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_signed_up
from allauth.account.utils import user_email
from django.conf import settings
from django.contrib.sessions.exceptions import InvalidSessionKey
from django.http import HttpRequest
from django.urls import NoReverseMatch
from django_hosts import reverse
from invitations.utils import get_invitation_model

import config.hosts
from transit_odp.bods.interfaces.plugins import get_notifications

Invitation = get_invitation_model()


# Note - couldn't seem to extend 'django-invitations' InvitationsAdapter class
# so just re-implementing it here
class AccountAdapter(DefaultAccountAdapter):
    PASSWORD_RESET_EMAIL_KEY = "password_reset_email"
    INVITE_EMAIL_KEY = "invite_email"
    VERIFICATION_EMAIL_KEY = "verification_email"
    ACCOUNT_VERIFIED_EMAIL_KEY = "account_verified_email"
    INVITATION_STARTED_KEY = "invitation_started"
    BACK_URL_KEY = "back_url"
    BULK_RESEND_INVITE_KEY = "bulk_resend_invite_org_ids"

    def __init__(self, *args, **kwargs):
        self._invitation = None
        super().__init__(*args, **kwargs)

    def stash_verification_email(self, request, email):
        """When the user tries to login with an unverified account, stash their
        email so we can display it in EmailVerificationSentView
        Note - there is a 'stash_user' method which could be used, but I'm not sure
        when and how this gets set/unset so it is better to have a separate variable
        we have control over
        """
        request.session[self.VERIFICATION_EMAIL_KEY] = email

    def stash_contains_verification_email(self, request) -> bool:
        return request.session.get(self.VERIFICATION_EMAIL_KEY, None) is not None

    def unstash_verification_email(self, request):
        return request.session.pop(self.VERIFICATION_EMAIL_KEY, None)

    def stash_account_verified_email(self, request, email):
        """Stashes email of verified account.

        When the user clicks the link in the verification email, their account is
        verified by invitations.views.AcceptInvite view"""
        request.session[self.ACCOUNT_VERIFIED_EMAIL_KEY] = email

    def stash_contains_account_verified_email(self, request) -> bool:
        return request.session.get(self.ACCOUNT_VERIFIED_EMAIL_KEY, None) is not None

    def unstash_account_verified_email(self, request):
        return request.session.pop(self.ACCOUNT_VERIFIED_EMAIL_KEY, None)

    def stash_invitation_started(self, request):
        """Stashes flag to indicate user has started sign up via invitation.

        The invitation link navigates to invitations.views.AcceptInvite view
        which initialises server-side state to handle the sign up process.
        AcceptInvite resets invitation_started to null so it can be set by the signup
        page.
        The signup page then uses this flag to ensure the user cannot call GET on the
        signup again (forces the user to restart flow if they refresh the page or
        navigate away)
        """
        request.session[self.INVITATION_STARTED_KEY] = True

    def stash_contains_invitation_started(self, request) -> bool:
        return request.session.get(self.INVITATION_STARTED_KEY, None) is not None

    def unstash_invitation_started(self, request) -> Optional[bool]:
        return request.session.pop(self.INVITATION_STARTED_KEY, None)

    def stash_password_reset_email(self, request, email):
        """Stashes email address in session storage

        This stash is used by `account_reset_password` view to stash email of user
        requesting a password reset.
        It is then retrieved on the subsequent confirmation view,
        `account_reset_password_done`, to display the email address sent the
        password reset email.
        """
        request.session[self.PASSWORD_RESET_EMAIL_KEY] = email

    def stash_contains_password_reset_email(self, request) -> bool:
        return request.session.get(self.PASSWORD_RESET_EMAIL_KEY, None) is not None

    def unstash_password_reset_email(self, request):
        return request.session.pop(self.PASSWORD_RESET_EMAIL_KEY, None)

    def stash_invite_email(self, request, email):
        """Stashes invite address in session storage

        This stash is used by InviteView to stash email of invited user before
        redirecting to InviteSuccessView where it is displayed in the confirmation
        message.
        """
        request.session[self.INVITE_EMAIL_KEY] = email

    def stash_contains_invite_email(self, request) -> bool:
        return request.session.get(self.INVITE_EMAIL_KEY, None) is not None

    def unstash_invite_email(self, request):
        return request.session.pop(self.INVITE_EMAIL_KEY, None)

    def stash_bulk_resend_invite_org_ids(self, request, org_ids):
        request.session[self.BULK_RESEND_INVITE_KEY] = org_ids

    def unstash_bulk_resend_invite_org_ids(self, request):
        return request.session.pop(self.BULK_RESEND_INVITE_KEY, [])

    def get_bulk_resend_invite_org_ids(self, request):
        return request.session.get(self.BULK_RESEND_INVITE_KEY, [])

    def is_open_for_signup(self, request: HttpRequest):
        """
        Note we replace InvitationsAdapter is_open_for_signup method since invites
        are always 'private'. Therefore we can toggle public registration with
        ACCOUNT_ALLOW_REGISTRATION while still sending invites to organisations
        """
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def get_user_signed_up_signal(self):
        return user_signed_up

    def respond_email_verification_sent(self, request, user):
        """
        Hook into here to stash user's email when they signup
        so we can display it on the email_verification_sent page
        """
        email = user_email(user)
        self.stash_verification_email(request, email)
        return super().respond_email_verification_sent(request, user)

    def get_logout_redirect_url(self, request):
        """
        Returns the URL to redirect to after the user logs out. Note that
        this method is also invoked if you attempt to log out while no users
        is logged in. Therefore, request.user is not guaranteed to be an
        authenticated user.
        """
        # FIXME: I wonder if this ever gets called, request.host is a string
        try:
            # use django_hosts reverse relative to current host
            return reverse(settings.ACCOUNT_LOGOUT_REDIRECT_URL, host=request.host.name)
        except NoReverseMatch:
            return super().get_logout_redirect_url(request)

    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.  Note
        that URLs passed explicitly (e.g. by passing along a `next`
        GET parameter) take precedence over the value returned here.
        """
        # I have no idea why this is needed but for testing
        # resolve_url(url) (parent) can not resolve the "LOGIN_REDIRECT_URL"
        # using django reverse. It can when used in the browser!!!
        host = config.hosts.PUBLISH_HOST
        try:
            if request.host == host or request.host.name == host:
                if request.user.is_agent_user:
                    return reverse("select-org", host=host)

                return reverse(
                    settings.PUBLISH_SELECT_DATA_URL,
                    host=host,
                    kwargs={"pk1": request.user.organisation_id},
                )

            # use django_hosts reverse relative to current host
            return reverse(settings.LOGIN_REDIRECT_URL, host=request.host)
        except NoReverseMatch:
            return super().get_login_redirect_url(request)

    def stash_back_url(self, request, url):
        """
        Example use case: stash HTTP_REFERER (feed-detail or manage-subscriptions)
        while on subscription confirm page, then unstash on success page. This
        sends user back to their origin page, avoiding the confirm page that's
        in the middle of the sequence.
        """
        request.session[self.BACK_URL_KEY] = url

    def stash_contains_back_url(self, request) -> bool:
        return request.session.get(self.BACK_URL_KEY, None) is not None

    def unstash_back_url(self, request):
        return request.session.pop(self.BACK_URL_KEY, None)

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        client = get_notifications()
        host = config.hosts.DATA_HOST
        invite_url = reverse(
            "account_confirm_email", args=[emailconfirmation.key], host=host
        )
        invite_url = request.build_absolute_uri(invite_url)
        client.send_verify_email_address_notification(
            contact_email=emailconfirmation.email_address.email, verify_link=invite_url
        )

    @property
    def invitation(self) -> Optional[Invitation]:
        """Invitation property that lazily loads the invitation"""
        if self._invitation is not None:
            # retrieve stored value
            return self._invitation

        email = self.request.session.get(self.ACCOUNT_VERIFIED_EMAIL_KEY, None)
        if email is None:
            # email is not stored in the session, bail out
            return None

        try:
            # Set Invitation organisation and role to new user
            self._invitation = Invitation.objects.get(email=email)
            return self._invitation
        except Invitation.DoesNotExist:
            raise InvalidSessionKey(
                "Could not retrieve invitation, please contact support"
            )

    def user_is_key_contact(self):
        """Returns a boolean True if user is a key contact False otherwise"""
        return self.invitation and self.invitation.is_key_contact
