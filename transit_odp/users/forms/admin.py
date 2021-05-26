from django import forms as forms
from django.contrib import auth
from django.contrib.auth import forms as auth_forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_hosts import reverse
from invitations.forms import CleanEmailMixin
from invitations.utils import get_invitation_model

from transit_odp.users.constants import AccountType

User = auth.get_user_model()
Invitation = get_invitation_model()

EMAIL_LABEL = _("Email*")
EMAIL_HELP_TEXT = _("Enter an email address in the right format, like name@example.com")
EMAIL_INVALID = EMAIL_HELP_TEXT  # TODO - make these different?
EMAIL_MISSING = _("Please provide an email")
USERNAME_DUPLICATE = _("This username has already been taken.")
PASSWORD_LABEL = _("Password*")
PASSWORD_HELP_TEXT = _("Your password should be at least 8 characters long.")
PASSWORD_INVALID = PASSWORD_HELP_TEXT
PASSWORD_MISSING = _("Please provide a password")
CONFIRM_PASSWORD_LABEL = _("Confirm new password*")
CURRENT_PASSWORD_LABEL = _("Current password")
NEW_PASSWORD_LABEL = _("New password")
PRIVACY_POLICY_URL = reverse("privacy-policy")
COOKIE_URL = reverse("cookie")
PRIVACY_TEXT = mark_safe(
    _(
        '<p class="govuk-body">By using this website, you agree to '
        f"the <a class='govuk-link' href='{PRIVACY_POLICY_URL}'>Privacy</a> and "
        f"<a class='govuk-link' href='{COOKIE_URL}'>Cookies</a> policies</p>"
    )
)
OPT_IN_USER_RESEARCH_OPERATOR = mark_safe(
    _(
        "If you are willing to be contacted as part of user research, "
        "please tick this box.*"
    )
)

OPT_IN_USER_RESEARCH_DEVELOPER = mark_safe(
    _(
        "Are you are willing to be contacted as part of user research to "
        "improve the service?*"
    )
)

SHARE_APP_USAGE = mark_safe(
    _(
        "If you're an application developer, would you be happy to freely share your "
        "app usage data with the Department for Transport?*"
    )
)


class UserChangeForm(auth_forms.UserChangeForm):
    class Meta(auth_forms.UserChangeForm.Meta):
        model = User

    opt_in_user_research = forms.BooleanField(
        required=False, label=OPT_IN_USER_RESEARCH_OPERATOR
    )

    share_app_usage = forms.BooleanField(required=False, label=SHARE_APP_USAGE)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["username"].required = False
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["dev_organisation"].required = False
        self.fields["description"].required = False

        self.fields[
            "opt_in_user_research"
        ].initial = self.instance.settings.opt_in_user_research

        self.fields["share_app_usage"].initial = self.instance.settings.share_app_usage

    def save(self, commit=True):
        user = super().save(commit=commit)

        description = self.cleaned_data.get("description")
        dev_organisation = self.cleaned_data.get("dev_organisation")
        if description is not None and dev_organisation is not None:
            user.description = description
            user.dev_organisation = dev_organisation
            user.save(update_fields=["description", "dev_organisation"])

        opt_in_user_research = self.cleaned_data.get("opt_in_user_research")
        share_app_usage = self.cleaned_data.get("share_app_usage")
        if opt_in_user_research is not None and share_app_usage is not None:
            user_settings = user.settings
            user_settings.opt_in_user_research = opt_in_user_research
            user_settings.share_app_usage = share_app_usage
            user_settings.save(
                update_fields=["opt_in_user_research", "share_app_usage"]
            )

        return user


class UserCreationForm(auth_forms.UserCreationForm):
    error_message = auth_forms.UserCreationForm.error_messages.update(
        {"duplicate_username": USERNAME_DUPLICATE}
    )
    opt_in_user_research = forms.BooleanField(
        required=False, label=OPT_IN_USER_RESEARCH_OPERATOR
    )

    share_app_usage = forms.BooleanField(required=False, label=SHARE_APP_USAGE)

    class Meta(auth_forms.UserCreationForm.Meta):
        model = User
        fields = auth_forms.UserCreationForm.Meta.fields + (
            "account_type",
            "first_name",
            "last_name",
            "email",
            "dev_organisation",
            "description",
            "opt_in_user_research",
            "share_app_usage",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].required = False
        self.fields["email"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["dev_organisation"].required = False
        self.fields["description"].required = False

        opt_in_user_research = self.fields["opt_in_user_research"]
        opt_in_user_research.label = OPT_IN_USER_RESEARCH_OPERATOR

        share_app_usage = self.fields["share_app_usage"]
        share_app_usage.label = SHARE_APP_USAGE

    account_type = forms.ChoiceField(
        choices=User.ACCOUNT_TYPE_CHOICES, initial=AccountType.org_admin.value
    )

    def clean_username(self):
        username = self.cleaned_data["username"]

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])

    def save(self, commit=True):
        user = super().save(commit=True)

        description = self.cleaned_data.get("description")
        dev_organisation = self.cleaned_data.get("dev_organisation")
        if description is not None and dev_organisation is not None:
            user.description = description
            user.dev_organisation = dev_organisation
            user.save(update_fields=["description", "dev_organisation"])

        opt_in_user_research = self.cleaned_data.get("opt_in_user_research")
        share_app_usage = self.cleaned_data.get("share_app_usage")
        if opt_in_user_research is not None and share_app_usage is not None:
            user_settings = user.settings
            user_settings.opt_in_user_research = opt_in_user_research
            user_settings.share_app_usage = share_app_usage
            user_settings.save(
                update_fields=["opt_in_user_research", "share_app_usage"]
            )

        return user


class InvitationAdminAddForm(CleanEmailMixin, forms.ModelForm):
    # 'inviter' can only be a site admin when inviting users from admin interface
    inviter = forms.ModelChoiceField(
        queryset=User.objects.filter(Q(is_superuser=True) | Q(is_staff=True))
    )

    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}),
    )

    class Meta:
        model = Invitation
        fields = ("email", "inviter", "organisation", "account_type")

    def __init__(self, *args, **kwargs):
        instance = kwargs.pop("instance", None)
        if instance is None:
            # initialise inviter to the logged in site admin user
            # initialise account_type to org_admin by default
            user = self.request.user
            instance = Invitation(
                inviter=user, account_type=AccountType.org_admin.value
            )
        super().__init__(instance=instance, *args, **kwargs)

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        # send email
        instance.send_invitation(self.request)
        return instance
