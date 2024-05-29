from crispy_forms.layout import ButtonHolder, Field, Layout
from transit_odp.crispy_forms_govuk.forms import GOVUKForm, GOVUKModelForm
from transit_odp.crispy_forms_govuk.layout import ButtonSubmit, LinkButton
from transit_odp.crispy_forms_govuk.layout.fields import (
    CheckboxMultipleField,
    CheckboxSingleField,
    LegendSize,
)
from django import forms
from django.contrib import auth
from django.utils.translation import gettext_lazy as _
from invitations.forms import CleanEmailMixin
from invitations.utils import get_invitation_model

from transit_odp.common.constants import DEFAULT_ERROR_SUMMARY
from transit_odp.common.layout import InlineFormset
from transit_odp.organisation.constants import PSV_LICENCE_AND_CHECKBOX
from transit_odp.organisation.forms.organisation_profile import (
    NOCFormset,
    OrganisationProfileForm,
    PSVFormset,
)
from transit_odp.organisation.models import Organisation
from transit_odp.site_admin.forms.base import (
    CHECKBOX_FIELD_KEY,
    STATUS_CHOICES,
    CheckboxFilterForm,
)
from transit_odp.site_admin.validators import validate_email_unique
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
        label=_("Key contact email (optional)"),
        required=False,
        widget=forms.TextInput(
            attrs={
                "type": "email",
                "size": "30",
                "class": "govuk-!-width-three-quarters",
            }
        ),
        validators=[validate_email_unique],
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

        self.nested_noc = NOCFormset(
            instance=self.instance,
            data=self.data if self.is_bound else None,
            files=self.files if self.is_bound else None,
        )

        self.nested_psv = PSVFormset(
            instance=self.instance,
            data=self.data if self.is_bound else None,
            files=self.files if self.is_bound else None,
        )

    def get_helper_properties(self):
        props = super().get_helper_properties()
        props.update({"nested_noc": self.nested_noc, "nested_psv": self.nested_psv})
        return props

    def get_layout(self):
        return Layout(
            "name",
            "short_name",
            "email",
            InlineFormset("nested_noc"),
            InlineFormset("nested_psv"),
            ButtonHolder(
                ButtonSubmit(name="submit", content=_("Submit")),
                LinkButton(url=self.cancel_url, content="Cancel"),
            ),
        )

    def is_valid(self):
        """
        Also validate the nested formsets.
        """
        is_valid = super().is_valid()
        noc = self.nested_noc.is_valid()
        psv_licence = self.nested_psv.is_valid()
        return all((is_valid, noc, psv_licence))

    def save(self, commit=True):
        inst = super().save(commit=commit)
        self.nested_noc.save(commit=commit)
        self.nested_psv.save(commit=commit)
        return inst


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


class OrganisationForm(OrganisationProfileForm):
    class Meta:
        model = Organisation
        fields = [
            "name",
            "short_name",
            "key_contact",
            "licence_required",
            "is_abods_global_viewer",
        ]
        labels = {
            "name": _("Organisation name"),
            "short_name": _("Organisation short name"),
        }

    def __init__(
        self, data=None, files=None, instance=None, cancel_url=None, *args, **kwargs
    ):
        super().__init__(
            data=data,
            files=files,
            instance=instance,
            cancel_url=cancel_url,
            *args,
            **kwargs,
        )
        name = self.fields["name"]
        name.widget.attrs.update({"class": "govuk-!-width-two-thirds"})
        self.fields.update(
            {
                "key_contact": forms.ModelChoiceField(
                    queryset=User.objects.filter(organisations=instance).filter(
                        account_type=AccountType.org_admin.value
                    ),
                    initial=instance.key_contact,
                    label=_("Key contact email (optional)"),
                    required=False,
                )
            }
        )
        self.fields.update(
            {
                "is_abods_global_viewer": forms.BooleanField(
                    label=_("Is ABODS Organisation"),
                    required=False,
                )
            }
        )
        key_contact = self.fields["key_contact"]
        self.fields["key_contact"].label_from_instance = lambda obj: obj.email
        key_contact.widget.attrs.update({"class": "govuk-!-width-full govuk-select"})

    def get_layout(self):
        if self.instance.licences.exists():
            checkbox = CheckboxSingleField(
                "licence_required",
                small_boxes=True,
                disabled=True,
                template="site_admin/snippets/licence_checkbox_field.html",
            )
        else:
            checkbox = CheckboxSingleField(
                "licence_required",
                small_boxes=True,
                template="site_admin/snippets/licence_checkbox_field.html",
            )
        return Layout(
            Field("name", wrapper_class="govuk-form-group govuk-!-margin-bottom-4"),
            Field(
                "short_name", wrapper_class="govuk-form-group govuk-!-margin-bottom-4"
            ),
            Field(
                "key_contact",
                wrapper_class="govuk-form-group govuk-!-margin-bottom-4",
            ),
            Field(
                "is_abods_global_viewer",
                wrapper_class="govuk-form-group govuk-!-margin-bottom-4",
            ),
            InlineFormset("nested_noc"),
            InlineFormset("nested_psv"),
            checkbox,
            ButtonHolder(
                ButtonSubmit(name="submit", content=_("Save")),
                LinkButton(url=self.cancel_url, content="Cancel"),
            ),
        )

    def clean(self):
        # At this point "licence required" is inverted from db
        org_data = self.cleaned_data

        # ☑ licence_required == False
        # ☐ licence_required == True
        licence_required = org_data.get("licence_required")

        if [error for error in self.nested_psv.errors if error != {}]:
            return org_data

        new_or_existing = []
        for data in self.nested_psv.cleaned_data:
            # filter out deleted or empty forms
            if data and not data["DELETE"]:
                new_or_existing.append(data)

        if new_or_existing and not licence_required:
            self.add_error(
                field="licence_required",
                error=(
                    'Untick "I do not have a PSV licence number" '
                    "checkbox to add licences"
                ),
            )

        if not new_or_existing and licence_required:
            self.add_error(
                field="licence_required",
                error=PSV_LICENCE_AND_CHECKBOX,
            )
        return org_data


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


class OperatorFilterForm(CheckboxFilterForm):
    form_label = "Operators"
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "govuk-!-width-full govuk-select"}),
    )

    def get_queryset(self):
        return Organisation.objects.add_first_letter()

    def get_layout(self):
        template = "common/forms/checkbox_filter_field.html"

        return Layout(
            CheckboxMultipleField(
                CHECKBOX_FIELD_KEY, legend_size=LegendSize.s, template=template
            ),
            "status",
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )
