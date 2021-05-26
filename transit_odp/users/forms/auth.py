import allauth.account.forms
from allauth.account.adapter import get_adapter
from allauth.account.forms import default_token_generator
from allauth.account.models import EmailAddress
from allauth.account.utils import (
    filter_users_by_email,
    send_email_confirmation,
    user_pk_to_url_str,
)
from allauth.utils import build_absolute_uri
from crispy_forms.layout import HTML, ButtonHolder, Layout
from crispy_forms_govuk.forms import GOVUKFormMixin
from crispy_forms_govuk.layout import ButtonSubmit, CheckboxField, LinkButton
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.common.contants import DEFAULT_ERROR_SUMMARY
from transit_odp.users import signals
from transit_odp.users.forms.admin import (
    CONFIRM_PASSWORD_LABEL,
    CURRENT_PASSWORD_LABEL,
    EMAIL_INVALID,
    EMAIL_LABEL,
    EMAIL_MISSING,
    NEW_PASSWORD_LABEL,
    OPT_IN_USER_RESEARCH_DEVELOPER,
    OPT_IN_USER_RESEARCH_OPERATOR,
    PASSWORD_HELP_TEXT,
    PASSWORD_LABEL,
    PASSWORD_MISSING,
    PRIVACY_TEXT,
    SHARE_APP_USAGE,
)
from transit_odp.users.models import AgentUserInvite


class LoginForm(GOVUKFormMixin, allauth.account.forms.LoginForm):
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Note we must call is_valid in order to set widget CSS classes when
        # there are field errors
        self.request = request

        # Add verification error to form errors (non-field errors)

        verification_error = "Email address not verified."

        if "data" in kwargs and "login" in kwargs["data"]:
            email = kwargs["data"]["login"]
            verification_error = (
                f"The email address <strong>{email}</strong> has not yet been verified."
                " We have sent you another confirmation email."
                ""
            )

        self.error_messages.update({"verification": mark_safe(verification_error)})

        attributes = {"placeholder": "", "class": "govuk-!-width-three-quarters"}

        login = self.fields["login"]
        login.label = EMAIL_LABEL
        login.error_messages.update(
            {"required": EMAIL_MISSING, "invalid": EMAIL_INVALID}
        )
        login.widget.attrs.update(attributes)

        password = self.fields["password"]
        password.label = PASSWORD_LABEL
        password.help_text = PASSWORD_HELP_TEXT
        password.error_messages.update({"required": PASSWORD_MISSING})
        password.widget.attrs.update(attributes)

    def get_layout(self):
        return Layout(
            "login", "password", ButtonSubmit("submit", "submit", content=_("Sign In"))
        )

    def get_form_error_title(self):
        form_error_title = _("There is a problem.")

        errors = self.errors.get_json_data()
        if not errors:
            return

        login_errors = errors.get("login", None)
        login_code = None
        if login_errors:
            login_code = login_errors[0]["code"]

        password_errors = errors.get("password", None)
        password_code = None
        if password_errors:
            password_code = password_errors[0]["code"]

        # For non-field errors, just show 'There is a problem'
        # non_field_errors = errors.get('__all__', None)

        login_required = login_code == "required"
        password_required = password_code == "required"
        if login_required and password_required:
            # Note I'm not going to handle other situations now, as the error codes
            # may be mixed
            form_error_title = _("The email and password boxes should not be empty")

        return form_error_title

    def clean(self):
        cleaned = super().clean()
        # Check that account is verified or display form error. Note AllAuth's default
        # behaviour is to redirect to the 'account_email_verification_sent' route
        user = self.user
        if user:
            has_verified_email = EmailAddress.objects.filter(
                user=user, verified=True
            ).exists()
            if not has_verified_email:
                send_email_confirmation(self.request, user, signup=False)
                raise ValidationError(self.error_messages["verification"])
        return cleaned


class BaseBODSSignupForm(GOVUKFormMixin, allauth.account.forms.SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attributes = {
            "placeholder": "",
            "class": "govuk-!-width-three-quarters",
        }

    def specific_custom_signup(self, request, user):
        # Implement this function for specific tasks for the different user account
        # types
        pass

    @transaction.atomic
    def custom_signup(self, request, user):
        # Common sign up tasks
        super().custom_signup(request, user)
        opt_in_user_research = self.cleaned_data.get("opt_in_user_research")
        user.settings.opt_in_user_research = opt_in_user_research
        user.settings.save()
        self.specific_custom_signup(request, user)


class DeveloperSignupForm(BaseBODSSignupForm):
    # Customise Signup form to add 'django-invitations' invitation data to the form
    first_name = forms.CharField(
        label=_("First Name*"),
    )
    last_name = forms.CharField(
        label=_("Last Name*"),
    )
    dev_organisation = forms.CharField(label=_("Organisation"), required=False)
    description = forms.CharField(required=False)
    opt_in_user_research = forms.ChoiceField(
        required=True, choices=((True, "Yes"), (False, "No"))
    )
    share_app_usage = forms.ChoiceField(
        required=True, choices=((True, "Yes"), (False, "No"))
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        first_name = self.fields["first_name"]
        first_name.required = True
        first_name.error_messages.update({"required": _("Please provide a first name")})
        first_name.widget.attrs.update(self._attributes)

        last_name = self.fields["last_name"]
        last_name.required = True
        last_name.error_messages.update({"required": _("Please provide a last name")})
        last_name.widget.attrs.update(self._attributes)

        dev_organisation = self.fields["dev_organisation"]
        dev_organisation.widget.attrs.update(self._attributes)

        description = self.fields["description"]
        description.widget = forms.Textarea(attrs={"rows": "3"})
        description.help_text = _(
            "Please use this section to describe how you intend to use the data. "
            "You may include the regions or areas you're interested in targeting, "
            "the products or apps you aim to develop/improve and what the API will "
            "enable you to do. "
        )
        description.widget.attrs.update(self._attributes)

        opt_in_user_research = self.fields["opt_in_user_research"]
        opt_in_user_research.label = OPT_IN_USER_RESEARCH_DEVELOPER
        opt_in_user_research.error_messages.update(
            {
                "required": _(
                    "Please choose if you are happy to be part of user research"
                )
            }
        )
        opt_in_user_research.widget = forms.RadioSelect()
        opt_in_user_research.widget.attrs.update(self._attributes)

        share_app_usage = self.fields["share_app_usage"]
        share_app_usage.label = SHARE_APP_USAGE
        share_app_usage.error_messages.update(
            {
                "required": _(
                    "Please choose if you are happy to share your app usage data"
                )
            }
        )
        share_app_usage.widget = forms.RadioSelect()
        share_app_usage.widget.attrs.update(self._attributes)

        email = self.fields["email"]
        email.label = EMAIL_LABEL
        email.error_messages.update(
            {"required": EMAIL_MISSING, "invalid": EMAIL_INVALID}
        )
        email.widget.attrs.update(self._attributes)

        password1 = self.fields["password1"]
        password1.label = PASSWORD_LABEL
        password1.help_text = PASSWORD_HELP_TEXT
        password1.error_messages.update({"required": PASSWORD_MISSING})
        password1.widget.attrs.update(self._attributes)

        password2 = self.fields["password2"]
        password2.label = CONFIRM_PASSWORD_LABEL
        password2.error_messages.update({"required": _("Please confirm your password")})
        password2.widget.attrs.update(self._attributes)

    def get_layout(self):
        return Layout(
            "first_name",
            "last_name",
            "dev_organisation",
            "description",
            CheckboxField(
                "share_app_usage", inline=True, dont_use_label_as_legend=True
            ),
            CheckboxField(
                "opt_in_user_research", inline=True, dont_use_label_as_legend=True
            ),
            "email",
            "password1",
            "password2",
            HTML(PRIVACY_TEXT),
            ButtonSubmit("submit", "submit", content=_("Create account")),
        )

    # Ensure privacy consent is saved. This is the expected approach,
    # but requires two step save user saved in super() then updated here, risking
    # inconsistency if the initial save succeeds but update fails
    # https://django-allauth.readthedocs.io/en/latest/forms.html#signup-allauth-account-forms-signupform
    def specific_custom_signup(self, request, user):
        share_app_usage = self.cleaned_data.get("share_app_usage")
        user.settings.share_app_usage = share_app_usage
        user.settings.save()
        user.dev_organisation = self.cleaned_data.get("dev_organisation")
        user.description = self.cleaned_data.get("description")
        user.save()


class OperatorSignupForm(BaseBODSSignupForm):
    opt_in_user_research = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        email = self.fields["email"]
        email.label = EMAIL_LABEL
        email.error_messages.update(
            {"required": EMAIL_MISSING, "invalid": EMAIL_INVALID}
        )
        email.widget.attrs.update(self._attributes)

        password1 = self.fields["password1"]
        password1.label = PASSWORD_LABEL
        password1.help_text = PASSWORD_HELP_TEXT
        password1.error_messages.update({"required": PASSWORD_MISSING})
        password1.widget.attrs.update(self._attributes)

        password2 = self.fields["password2"]
        password2.label = CONFIRM_PASSWORD_LABEL
        password2.error_messages.update({"required": _("Confirm your password")})
        password2.widget.attrs.update(self._attributes)

        opt_in_user_research = self.fields["opt_in_user_research"]
        opt_in_user_research.label = OPT_IN_USER_RESEARCH_OPERATOR

    def get_layout(self):
        return Layout(
            "email",
            "password1",
            "password2",
            HTML(PRIVACY_TEXT),
            CheckboxField("opt_in_user_research"),
            ButtonSubmit("submit", "submit", content=_("Create account")),
        )

    def specific_custom_signup(self, request, user):
        adapter = get_adapter(request)
        invite = adapter.invitation
        organisation = invite.organisation
        # an org user should always have an invite and belong to an organisation
        user.email = invite.email
        user.account_type = invite.account_type

        if adapter.user_is_key_contact():
            organisation.key_contact = user

        if not organisation.is_active:
            # If we are adding new users to an organisation then it must be active.
            organisation.is_active = True

        user.save()
        # Organisation added after user.account_type is set and saved
        user.organisations.add(organisation)
        organisation.save()
        # Organisation added after user.account_type is set and saved
        signals.user_accepted.send(None, invite=invite, user=user)


class AgentSignupForm(OperatorSignupForm):
    agent_organisation = forms.CharField(label=_("Organisation*"), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        agent_organisation = self.fields["agent_organisation"]
        agent_organisation.widget.attrs.update(self._attributes)
        agent_organisation.error_messages.update(
            {"required": _("Please provide an organisation")}
        )

    def get_layout(self):
        return Layout(
            "email",
            "agent_organisation",
            "password1",
            "password2",
            HTML(PRIVACY_TEXT),
            CheckboxField("opt_in_user_research"),
            ButtonSubmit("submit", "submit", content=_("Create account")),
        )

    def specific_custom_signup(self, request, user):
        adapter = get_adapter(request)
        invite = adapter.invitation
        organisation = invite.organisation
        # an org user should always have an invite and belong to an organisation
        user.email = invite.email
        user.account_type = invite.account_type
        user.agent_organisation = self.cleaned_data.get("agent_organisation")
        invite.agent_user_invite.agent = user
        invite.agent_user_invite.status = AgentUserInvite.ACCEPTED
        invite.agent_user_invite.save()

        if not organisation.is_active:
            # If we are adding new users to an organisation then it must be active.
            organisation.is_active = True

        user.save()
        # Organisation added after user.account_type is set and saved
        user.organisations.add(organisation)
        organisation.save()
        # Organisation added after user.account_type is set and saved
        signals.user_accepted.send(None, invite=invite, user=user)


class ResetPasswordForm(GOVUKFormMixin, allauth.account.forms.ResetPasswordForm):
    form_error_title = DEFAULT_ERROR_SUMMARY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        attributes = {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        email = self.fields["email"]
        email.label = EMAIL_LABEL
        email.error_messages.update(
            {"required": EMAIL_MISSING, "invalid": EMAIL_INVALID}
        )
        email.widget.attrs.update(attributes)

    def get_layout(self):
        return Layout("email", ButtonSubmit("submit", "submit", content=_("Continue")))

    def clean_email(self):
        return self.cleaned_data["email"]

    def save(self, request, **kwargs):
        # reimplemented super().save but use notifications instead
        client = get_notifications()

        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)
        self.users = filter_users_by_email(email, is_active=True)

        token_generator = kwargs.get("token_generator", default_token_generator)

        for user in self.users:

            temp_key = token_generator.make_token(user)
            path = reverse(
                "account_reset_password_from_key",
                kwargs=dict(uidb36=user_pk_to_url_str(user), key=temp_key),
            )
            url = build_absolute_uri(request, path)
            client.send_password_reset_notification(
                contact_email=user.email, reset_link=url
            )

        return self.cleaned_data["email"]


class ChangePasswordForm(GOVUKFormMixin, allauth.account.forms.ChangePasswordForm):
    form_error_title = DEFAULT_ERROR_SUMMARY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        attributes = {"placeholder": "", "class": "govuk-!-width-three-quarters"}

        oldpassword = self.fields["oldpassword"]
        oldpassword.label = CURRENT_PASSWORD_LABEL
        oldpassword.error_messages.update(
            {"required": _("Enter your current password")}
        )
        oldpassword.widget.attrs.update(attributes)

        password1 = self.fields["password1"]
        password1.label = NEW_PASSWORD_LABEL
        # password1.help_text = PASSWORD_HELP_TEXT
        password1.error_messages.update({"required": _("Enter your new password")})
        password1.widget.attrs.update(attributes)

        password2 = self.fields["password2"]
        password2.label = CONFIRM_PASSWORD_LABEL
        password2.error_messages.update({"required": _("Confirm your new password")})
        password2.widget.attrs.update(attributes)

    def get_layout(self):
        return Layout(
            "oldpassword",
            "password1",
            "password2",
            ButtonHolder(
                ButtonSubmit("submit", "submit", content=_("Reset password")),
                LinkButton(reverse("users:settings")),
            ),
        )


class ResetPasswordKeyForm(GOVUKFormMixin, allauth.account.forms.ResetPasswordKeyForm):
    form_error_title = DEFAULT_ERROR_SUMMARY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        attributes = {"placeholder": "", "class": "govuk-!-width-one-half"}

        password1 = self.fields["password1"]
        password1.help_text = PASSWORD_HELP_TEXT
        password1.error_messages.update({"required": _("Enter your new password")})
        password1.widget.attrs.update(attributes)

        password2 = self.fields["password2"]
        password2.error_messages.update({"required": _("Confirm your new password")})
        password2.widget.attrs.update(attributes)

    def get_layout(self):
        return Layout(
            "password1",
            "password2",
            ButtonSubmit("submit", "submit", content=_("Reset password")),
        )
