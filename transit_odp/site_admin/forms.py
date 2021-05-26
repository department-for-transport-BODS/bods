from crispy_forms.layout import ButtonHolder, Field, Layout
from crispy_forms_govuk.forms import GOVUKForm, GOVUKModelForm
from crispy_forms_govuk.layout import ButtonSubmit, LinkButton
from django import forms
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from invitations.forms import CleanEmailMixin
from invitations.utils import get_invitation_model

from transit_odp.common.contants import DEFAULT_ERROR_SUMMARY
from transit_odp.common.layout import InlineFormset
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.forms.organisation_profile import NOCFormset
from transit_odp.organisation.models import Organisation
from transit_odp.users.constants import AccountType
from transit_odp.users.forms.admin import (
    EMAIL_HELP_TEXT,
    EMAIL_INVALID,
    EMAIL_LABEL,
    EMAIL_MISSING,
)

User = auth.get_user_model()
Invitation = get_invitation_model()


class OrganisationNameForm(GOVUKModelForm, CleanEmailMixin):
    form_error_title = DEFAULT_ERROR_SUMMARY
    errors_template = "organisation/organisation_profile_form/errors.html"

    class Meta:
        model = Organisation
        fields = ("name", "short_name")

    email = forms.EmailField(
        label=_("Key contact email"),
        required=True,
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "size": "30",
                "class": "govuk-!-width-three-quarters",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.cancel_url = kwargs.pop("cancel_url")
        super().__init__(*args, **kwargs)

        name = self.fields["name"]
        name.label = _("Organisation name")
        name.widget.attrs.update({"class": "govuk-!-width-three-quarters"})
        name.error_messages.update({"required": _("Enter the organisation name")})

        short_name = self.fields["short_name"]
        short_name.label = _("Organisation short name")
        short_name.widget.attrs.update({"class": "govuk-!-width-three-quarters"})
        short_name.error_messages.update(
            {"required": _("Enter the organisation short name")}
        )

        self.nested = NOCFormset(
            instance=self.instance,
            data=self.data if self.is_bound else None,
            files=self.files if self.is_bound else None,
        )

    def get_layout(self):
        return Layout(
            "name",
            "short_name",
            "email",
            InlineFormset("nested"),
            ButtonHolder(
                ButtonSubmit(name="submit", content=_("Send Invitation")),
                LinkButton(url=self.cancel_url, content="Cancel"),
            ),
        )


class OrganisationContactEmailForm(CleanEmailMixin, GOVUKForm):
    """
    The contact form derives from CleanEmailMixin since it is used to clean
    the email to send the invite. This provides extra validation around email,
    such as checking its not already in use / been invited.
    """

    form_tag = False
    form_error_title = _("There is a problem")

    email = forms.EmailField(
        label=_("E-mail"),
        required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        email = self.fields["email"]
        email.label = EMAIL_LABEL
        email.help_text = EMAIL_HELP_TEXT
        email.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )

        email.error_messages.update(
            {"required": EMAIL_MISSING, "invalid": EMAIL_INVALID}
        )

    def get_layout(self):
        return Layout("email")


class OrganisationForm(GOVUKModelForm):
    errors_template = "organisation/organisation_profile_form/errors.html"

    class Meta:
        model = Organisation
        fields = ["name", "short_name", "key_contact"]
        labels = {
            "name": _("Organisation name"),
            "short_name": _("Organisation short name"),
        }

    def __init__(
        self, data=None, files=None, instance=None, cancel_url=None, *args, **kwargs
    ):
        super().__init__(data=data, files=files, instance=instance, *args, **kwargs)
        self.cancel_url = cancel_url

        # Create a nested formset
        self.nested = NOCFormset(
            instance=instance,
            data=data if self.is_bound else None,
            files=files if self.is_bound else None,
        )

        name = self.fields["name"]
        name.widget.attrs.update({"class": "govuk-!-width-two-thirds"})

        short_name = self.fields["short_name"]
        short_name.widget.attrs.update({"class": "govuk-!-width-two-thirds"})

        self.fields.update(
            {
                "key_contact": forms.ModelChoiceField(
                    queryset=User.objects.filter(organisations=instance).filter(
                        account_type=AccountType.org_admin.value
                    ),
                    initial=instance.key_contact,
                    label=_("Key contact email"),
                )
            }
        )
        key_contact = self.fields["key_contact"]
        self.fields["key_contact"].label_from_instance = lambda obj: obj.email
        key_contact.widget.attrs.update({"class": "govuk-!-width-full govuk-select"})

    def get_helper_properties(self):
        props = super().get_helper_properties()
        # Add nested formset to helper properties. This will expose it in the context
        props.update({"nested": self.nested})
        return props

    def get_layout(self):
        return Layout(
            Field("name", wrapper_class="govuk-form-group govuk-!-margin-bottom-4"),
            Field(
                "short_name", wrapper_class="govuk-form-group govuk-!-margin-bottom-4"
            ),
            Field(
                "key_contact",
                wrapper_class="govuk-form-group govuk-!-margin-bottom-4",
            ),
            InlineFormset("nested"),
            ButtonHolder(
                ButtonSubmit(name="submit", content=_("Save")),
                LinkButton(url=self.cancel_url, content="Cancel"),
            ),
        )

    def is_valid(self):
        """
        Also validate the nested formsets.
        """
        is_valid = super().is_valid()
        nested = self.nested.is_valid()
        return is_valid and nested

    def save(self, commit=True):
        self.instance.key_contact = self.cleaned_data["key_contact"]
        inst = super().save(commit=commit)
        self.nested.save(commit=commit)
        return inst


class OrganisationFilterForm(GOVUKForm):
    form_method = "get"
    form_tag = False

    status = forms.ChoiceField(
        choices=(("", "All statuses"), (0, "Active"), (1, "Pending"), (2, "Inactive")),
        required=False,
    )
    name = forms.ChoiceField(
        choices=(("", "All statuses"), (0, "Active"), (1, "Pending"), (2, "Inactive")),
        required=False,
    )

    def get_layout(self):
        return Layout(
            Field("status", css_class="govuk-!-width-full"),
            Field("name", css_class="govuk-!-width-full"),
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )


class BulkResendInvitesForm(forms.Form):
    form_method = "get"
    bulk_invite = forms.BooleanField(required=False, initial=False)
    invites = forms.IntegerField(required=False)

    def __init__(self, *args, orgs=None, **kwargs):
        self.orgs_qs = orgs
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.data.get("bulk_invite", False) and not self.data.getlist("invites"):
            raise ValidationError(
                _("Please select organisation(s) from below to resend invitation")
            )

    def clean_invites(self):
        org_ids = [int(org_id) for org_id in self.data.getlist("invites", [])]
        return org_ids

    def _post_clean(self):
        if (
            self.orgs_qs.filter(id__in=self.cleaned_data["invites"])
            .exclude(status="pending")
            .exists()
        ):
            self.add_error(
                None,
                ValidationError(
                    _(
                        "You cannot send invites to already active organisations, "
                        "please select pending ones"
                    )
                ),
            )


class BaseDatasetSearchFilterForm(GOVUKForm):
    form_method = "get"
    form_tag = False

    status = forms.ChoiceField(
        choices=(
            ("", "All statuses"),
            (FeedStatus.live.value, "Published"),
            (FeedStatus.success.value, "Draft"),
            (FeedStatus.expired.value, "Expired"),
            (FeedStatus.inactive.value, "Inactive"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].widget.attrs.update({"aria-label": "Filter by"})

    def get_layout(self):
        return Layout(
            Field("status", css_class="govuk-!-width-full"),
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )


class TimetableSearchFilterForm(BaseDatasetSearchFilterForm):
    pass


class AVLSearchFilterForm(BaseDatasetSearchFilterForm):
    status = forms.ChoiceField(
        choices=(
            ("", "All statuses"),
            (FeedStatus.live.value, "Published"),
            (FeedStatus.error.value, "Error"),
            (FeedStatus.inactive.value, "Deactivated"),
        ),
        required=False,
    )


class EditNotesForm(GOVUKModelForm):
    class Meta:
        model = User
        fields = ["notes"]
        labels = {"notes": "Notes"}
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 5, "cols": 20}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
