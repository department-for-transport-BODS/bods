from crispy_forms.layout import HTML, ButtonHolder, Layout
from transit_odp.frontend.forms import GOVUKModelForm
from transit_odp.frontend.layout import (
    ButtonSubmit,
    CheckboxField,
    LegendSize,
    LinkButton,
    RadioAccordion,
    RadioAccordionGroup,
)
from django import forms as forms
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.http import HttpResponseServerError
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse
from invitations.adapters import get_invitations_adapter
from invitations.exceptions import AlreadyAccepted
from invitations.forms import CleanEmailMixin
from invitations.utils import get_invitation_model

import config.hosts
from transit_odp.organisation.constants import ORG_NOT_YET_INVITED
from transit_odp.users.constants import AccountType
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.models import User as UserModel

User: UserModel = auth.get_user_model()
Invitation = get_invitation_model()


class InvitationFirstForm(CleanEmailMixin, GOVUKModelForm):
    class Meta:
        model = Invitation
        fields = ["email"]

    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}),
    )

    def __init__(
        self,
        cancel_url,
        *args,
        request=None,
        instance=None,
        organisation=None,
        **kwargs,
    ):
        # inviter and organisation are hidden from the user. Inviter and organisation
        # set here so that organisation mismatch doesn't cause error when
        # GOVUKModelForm calls clean method to set the initial error classes
        self.request = request
        current_user = self.request.user
        self._agent_user = None
        self._existing_invite = None

        if instance is not None:
            instance.inviter = current_user
            instance.organisation = (
                current_user.organisation
                if current_user.organisation is not None and organisation is None
                else organisation
            )

        super().__init__(*args, instance=instance, **kwargs)
        # The organisation's first invited user is forced to be an org admin as well as
        # the key contact
        self.instance.is_key_contact = (
            False
            if organisation is None
            else (organisation.get_status() == ORG_NOT_YET_INVITED)
        )
        self.instance.account_type = AccountType.org_admin.value
        self.cancel_url = cancel_url

        email = self.fields["email"]
        email.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )
        email.error_messages.update({"required": _("Enter a valid email address")})

    def get_layout(self):
        return Layout(
            "email",
            HTML(
                """<div style="display: inline-flex;" class="govuk-!-padding-bottom-5">
                <i class="fas fa-exclamation-circle fa-3x"></i>
                <p class="govuk-body
                          govuk-!-font-weight-bold
                          govuk-!-padding-left-2">
                    Please note that the first user invited to an organisation will be
                    assigned the Admin status automatically.<br>
                    <br>
                    Admin users will be able to add and/or remove other user's accounts
                    from the open data service.
                </p>
                </div>"""
            ),
            ButtonHolder(
                ButtonSubmit("submit", "submit", content=_("Send invitation")),
                LinkButton(url=self.cancel_url, content=_("Cancel")),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        # make sure inviter belongs to organisation
        inviter = self.instance.inviter
        organisation = self.instance.organisation

        if inviter is not None and inviter.is_site_admin:
            return cleaned_data

        if (
            inviter is None
            or organisation is None
            or (inviter.organisation != organisation)
        ):
            return HttpResponseServerError()
        else:
            return cleaned_data

    def validate_invitation(self, email):
        if User.objects.filter(email=email).exists():
            raise AlreadyAccepted
        try:
            # This is by definition an old invite if it exists
            self._existing_invite = Invitation.objects.get(email=email)
        except Invitation.DoesNotExist:
            pass

        return True

    def _post_clean(self):
        if self.errors:
            # Skip _post_clean if the form is already invalid, don't want to have
            # Model.clean non-field errors
            return
        self._validate_unique = False
        super()._post_clean()

    def _get_or_create_standard_invite(self, *args, **kwargs):
        """Get or create a standard user invitation."""
        site = get_current_site(self.request)
        if self._existing_invite is None:
            standard_invite = super().save(*args, **kwargs)
        else:
            standard_invite = self._existing_invite
            standard_invite.accepted = False
            standard_invite.organisation = self.instance.organisation
            standard_invite.account_type = self.instance.account_type
            standard_invite.inviter = self.instance.inviter
            standard_invite.key = get_random_string(64).lower()
            standard_invite.is_key_contact = self.instance.is_key_contact
            standard_invite.save()
        standard_invite.send_invitation(self.request, *args, site=site, **kwargs)
        return standard_invite

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Save an invitation."""
        standard_invite = self._get_or_create_standard_invite(*args, **kwargs)
        return standard_invite


class InvitationSubsequentForm(InvitationFirstForm):
    ADMIN_ID = "admin"
    STAFF_ID = "staff"
    AGENT_ID = "agent"

    class Meta:
        model = Invitation
        fields = ["email", "account_type"]

    account_type = forms.CharField(
        label=_("User type"),
        required=True,
        widget=forms.HiddenInput(),
    )

    def __init__(
        self,
        cancel_url,
        *args,
        request=None,
        instance=None,
        organisation=None,
        **kwargs,
    ):
        super().__init__(
            cancel_url,
            *args,
            request=request,
            instance=instance,
            organisation=organisation,
            **kwargs,
        )
        self.instance.is_key_contact = False

    def get_layout(self):
        agent_guidance_link = (
            reverse("guidance:support-bus_operators", host=config.hosts.PUBLISH_HOST)
            + "?section=agents"
        )
        admin_hint_text = (
            "Note: Admin users will be able to add and/or remove other "
            "user's accounts from the open data service."
        )
        agent_warning_text = (
            "Please note that even if you nominate an agent, it is still your legal "
            "obligation to ensure that your data is up to date. It is recommended you "
            "have consistent communication with your agent and have contracts agreed "
            "with them external to this platform. Please read more about the guidance "
            f'on agents <a class="govuk-link" href="{agent_guidance_link}">here</a>.'
        )
        return Layout(
            "email",
            "account_type",
            RadioAccordion(
                RadioAccordionGroup(
                    "Admin - key account holders of the organisation",
                    HTML(f'<p class="govuk-hint">{admin_hint_text}</p>'),
                    css_id=self.ADMIN_ID,
                ),
                RadioAccordionGroup(
                    "Standard - staff of the organisation",
                    css_id=self.STAFF_ID,
                ),
                RadioAccordionGroup(
                    "Agent - agents acting on behalf of the organisation",
                    HTML(
                        f"""<div style="display: inline-flex;">
                        <i class="fas fa-exclamation-circle fa-3x"></i>
                        <p class="govuk-body
                                  govuk-!-font-weight-bold
                                  govuk-!-padding-left-2">
                         {agent_warning_text}
                        </p>
                        </div>"""
                    ),
                    css_id=self.AGENT_ID,
                ),
                legend=_("Choose the account type"),
                legend_size=LegendSize.s,
            ),
            ButtonHolder(
                ButtonSubmit("submit", "submit", content=_("Send invitation")),
                LinkButton(url=self.cancel_url, content=_("Cancel")),
            ),
        )

    def clean_email(self):
        """
        Overrides CleanEmailMixin so we can invite agent users
        to multiple organisations without there being an exception
        :returns str email
        """
        if self.data.get("selected_item") != self.AGENT_ID:
            # resume normal invite flow
            return super().clean_email()

        email = self.cleaned_data["email"]
        email = get_invitations_adapter().clean_email(email)
        try:
            self._agent_user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return super().clean_email()

        if self._agent_user.account_type != AccountType.agent_user.value:
            raise forms.ValidationError(
                _("An active non-agent user is using this e-mail address")
            )
        if self._agent_user.organisations.filter(
            id=self.instance.organisation.id
        ).exists():
            raise forms.ValidationError(
                _("This agent is already active for this organisation")
            )

        return email

    def clean_account_type(self):
        selected_item = self.data.get("selected_item")
        account_type_mapper = {
            self.AGENT_ID: AccountType.agent_user.value,
            self.ADMIN_ID: AccountType.org_admin.value,
            self.STAFF_ID: AccountType.org_staff.value,
        }
        try:
            account_type = account_type_mapper[selected_item]
        except KeyError:
            error = forms.ValidationError(
                mark_safe(_('<a href="#admin-radio">Choose the account type.</a>'))
            )
            raise error

        self.cleaned_data["account_type"] = account_type
        return account_type

    def _send_existing_agent_user_invite(self):
        """Send an agent invite to an agent user that already exists on the system.

        No sign-up link is sent, just a notification to check the accounts section.
        """
        standard_invite = self.instance
        try:
            agent_invite = AgentUserInvite.objects.get(
                agent=self._agent_user, organisation=standard_invite.organisation
            )
        except AgentUserInvite.DoesNotExist:
            agent_invite = AgentUserInvite(
                agent=self._agent_user, organisation=standard_invite.organisation
            )

        agent_invite.inviter = standard_invite.inviter
        agent_invite.status = AgentUserInvite.PENDING
        agent_invite.save()
        agent_invite.send_confirmation()
        return standard_invite

    def _update_or_create_agent_invite(self, standard_invite):
        try:
            # Case where a new agent has been added but has not accepted
            # then someone tries to add them again possibly from
            # a different organisation.
            agent_invite = AgentUserInvite.objects.get(invitation=standard_invite)
            agent_invite.inviter = standard_invite.inviter
            agent_invite.organisation = standard_invite.organisation
            agent_invite.save()
        except AgentUserInvite.DoesNotExist:
            AgentUserInvite.objects.create(
                agent=None,
                invitation=standard_invite,
                inviter=standard_invite.inviter,
                status=AgentUserInvite.PENDING,
                organisation=standard_invite.organisation,
            )

    @transaction.atomic
    def save(self, *args, **kwargs):
        """Save an invitation."""
        account_type = self.instance.account_type

        if self._agent_user is None:
            standard_invite = self._get_or_create_standard_invite(*args, **kwargs)

            if account_type == AccountType.agent_user.value:
                self._update_or_create_agent_invite(standard_invite)
            return standard_invite

        return self._send_existing_agent_user_invite()


class UserEditForm(GOVUKModelForm):
    class Meta:
        model = get_user_model()
        fields = ["username", "email", "account_type"]

    username = forms.CharField(label=_("Username"), required=True)

    email = forms.EmailField(
        label=_("Email"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}),
    )

    account_type = forms.ChoiceField(
        label=_("User type"),
        choices=(
            (AccountType.org_admin.value, _("Admin")),
            (AccountType.org_staff.value, _("Standard")),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    def __init__(self, cancel_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cancel_url = cancel_url

    def get_layout(self):
        return Layout(
            "username",
            "email",
            CheckboxField("account_type", "User type", id="account_type"),
            ButtonHolder(
                ButtonSubmit("submit", "submit", content=_("Save")),
                LinkButton(url=self.cancel_url, content="Cancel"),
            ),
        )
