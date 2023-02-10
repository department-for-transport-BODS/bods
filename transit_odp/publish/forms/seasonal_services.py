from crispy_forms.layout import HTML, ButtonHolder, Div, Layout
from crispy_forms_govuk.forms import GOVUKModelForm
from crispy_forms_govuk.layout import LinkButton
from crispy_forms_govuk.layout.fields import Field
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.forms import NumberInput
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.common.constants import DEFAULT_ERROR_SUMMARY
from transit_odp.organisation.models import Licence, SeasonalService
from transit_odp.publish.forms.constants import CONTINUE_BUTTON, SAVE_BUTTON, SEPARATOR
from transit_odp.timetables.tables import get_table_page


def cancel_seasonal_service(org_id: int, page: str) -> LinkButton:
    return LinkButton(
        reverse("seasonal-service", kwargs={"pk1": org_id}, host=PUBLISH_HOST)
        + get_table_page(page),
        content="Cancel",
    )


class FieldNoErrors(Field):
    """
    Override Field class but supress the group error so each
    date does not have an individual error bar
    """

    def render(self, form, form_style, context, **kwargs):
        context["suppress_form_group_error"] = True
        return super().render(form, form_style, context, **kwargs)


class DateDiv(Div):
    """
    Override Div class so error bar is added to container if
    errors are detected in its fields
    """

    def render(self, form, form_style, context, **kwargs):
        show_error = False
        for field in self.fields:
            bound_field = form[field.fields[0]]
            if bound_field.errors:
                show_error = True
                break

        if show_error:
            self.css_class += " govuk-form-group--error"

        return super().render(form, form_style, context, **kwargs)


class LicenceNumberForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY
    subheading = _(
        "Select the PSV licence number to add seasonal service operating dates."
    )

    class Meta:
        model = SeasonalService
        fields = ("licence",)

    def __init__(self, *args, **kwargs):
        self.org_id = kwargs.pop("org_id", None)
        self.page = kwargs.pop("page", None)
        super().__init__(*args, **kwargs)
        self.fields.update(
            {
                "licence": forms.ModelChoiceField(
                    queryset=Licence.objects.filter(organisation_id=self.org_id),
                    required=True,
                    label="PSV licence number",
                    empty_label=_("Select PSV licence number"),
                )
            }
        )
        number_field = self.fields["licence"]
        number_field.label_from_instance = lambda obj: obj.number
        number_field.widget.attrs.update({"class": "govuk-!-width-full"})

    def get_layout(self):
        return Layout(
            Div("licence", css_class="licence"),
            SEPARATOR,
            ButtonHolder(
                CONTINUE_BUTTON,
                cancel_seasonal_service(self.org_id, self.page),
                css_class="buttons",
            ),
        )


class BaseForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY

    start = forms.DateField(
        required=True,
        label=_("Service begins on"),
        error_messages={
            "invalid": _("Error first date"),
            "required": _("This date is required"),
        },
        widget=NumberInput(attrs={"type": "date"}),
    )
    end = forms.DateField(
        required=True,
        label=_("Service ends on"),
        error_messages={
            "invalid": _("Error last date"),
            "required": _("This date is required"),
        },
        widget=NumberInput(attrs={"type": "date"}),
        validators=(
            MinValueValidator(
                limit_value=lambda: timezone.now().date(),
                message=("End date cannot be in the past"),
            ),
        ),
    )

    class Meta:
        model = SeasonalService
        fields = ("start", "end")

    def clean(self):
        cleaned_data = self.cleaned_data
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        if start is None or end is None:
            return cleaned_data

        if start > end:
            raise ValidationError("Start date must be earlier than end date")
        return cleaned_data


class EditRegistrationCodeDateForm(BaseForm):
    registration_code = forms.IntegerField(
        required=True,
        label=_("Service code"),
        error_messages={"required": _("Enter a service code in the box below")},
    )

    class Meta:
        model = SeasonalService
        fields = ("registration_code", "start", "end")

    def __init__(self, *args, **kwargs):
        self.licence = kwargs.pop("licence", None)
        self.org_id = kwargs.pop("org_id", None)
        self.page = kwargs.pop("page", None)
        super().__init__(*args, **kwargs)

    def get_layout(self):
        help_modal = render_to_string(
            "publish/snippets/help_modals/seasonal_services.html"
        )
        edit_snippet = render_to_string(
            "publish/seasonal_services/edit_service_code_snippet.html",
            context={
                "link": reverse(
                    "add-seasonal-service",
                    kwargs={"pk1": self.org_id},
                    host=PUBLISH_HOST,
                ),
                "number": self.licence.number,
            },
        )

        return Layout(
            HTML(edit_snippet),
            Field(
                "registration_code",
                template="publish/seasonal_services/service_code_widget.html",
            ),
            HTML(
                format_html(
                    '<h2 class="govuk-heading-s">Service operating dates {}</h2>',
                    help_modal,
                )
            ),
            DateDiv(
                FieldNoErrors("start", wrapper_class="date"),
                FieldNoErrors("end", wrapper_class="date"),
                css_class="date-container",
            ),
            SEPARATOR,
            ButtonHolder(
                SAVE_BUTTON,
                cancel_seasonal_service(self.org_id, self.page),
                css_class="buttons",
            ),
        )

    def clean_registration_code(self):
        registration_code = self.cleaned_data["registration_code"]
        exists = SeasonalService.objects.filter(
            licence=self.licence, registration_code=registration_code
        ).exists()
        if exists:
            raise ValidationError(
                "This service code has already been set up with a date range"
            )
        return registration_code


class EditDateForm(BaseForm):
    def __init__(self, *args, **kwargs):
        self.org_id = kwargs.pop("org_id", None)
        self.page = kwargs.pop("page", None)
        super().__init__(*args, **kwargs)

    def get_layout(self):
        help_modal = render_to_string(
            "publish/snippets/help_modals/seasonal_services.html"
        )
        edit_snippet = render_to_string(
            "publish/seasonal_services/edit_page_service_code_snippet.html",
            context={"form": self},
        )

        return Layout(
            HTML(edit_snippet),
            HTML(
                format_html(
                    '<h2 class="govuk-heading-s">Service operating dates {}</h2>',
                    help_modal,
                ),
            ),
            DateDiv(
                FieldNoErrors("start", wrapper_class="date"),
                FieldNoErrors("end", wrapper_class="date"),
                css_class="date-container",
            ),
            SEPARATOR,
            ButtonHolder(
                SAVE_BUTTON,
                cancel_seasonal_service(self.org_id, self.page),
                css_class="buttons",
            ),
        )


class DeleteForm(forms.Form):
    id = forms.IntegerField(required=True)

    def __init__(self, *args, org_id=None, **kwargs):
        self.org_id = org_id
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        id_ = self.cleaned_data.get("id")
        return SeasonalService.objects.filter(
            licence__organisation__id=self.org_id, id=id_
        ).delete()
