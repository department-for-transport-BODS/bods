from crispy_forms.layout import Div, Field, Layout
from crispy_forms_govuk.forms import GOVUKFormMixin
from crispy_forms_govuk.layout import ButtonElement
from crispy_forms_govuk.layout.fields import HiddenField
from django import forms
from django.utils.translation import gettext_lazy as _

from transit_odp.common.layout import TD, TR
from transit_odp.organisation.models import Licence, ServiceCodeExemption

DUPLICATE_SERVICE_CODE = _(
    "Duplicate service code added; Please check the code and try again"
)


class ServiceCodeExemptionsForm(GOVUKFormMixin, forms.ModelForm):
    class Meta:
        model = ServiceCodeExemption
        fields = ["licence", "registration_code", "justification"]

    is_formset = True
    licence = forms.ModelChoiceField(
        label=_("PSV Licence number"),
        queryset=Licence.objects.all(),
        empty_label=_("Select PSV"),
        required=True,
    )

    registration_code = forms.IntegerField(
        label=_("Service Code"),
        widget=forms.NumberInput(
            attrs={
                "placeholder": _("Enter service code"),
            }
        ),
        error_messages={"required": "Enter a service code to continue."},
        required=True,
        min_value=1,
    )

    justification = forms.CharField(
        label=_("Justification for exemption (140 characters maximum)"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Exemption reason (optional)"),
            }
        ),
        required=False,
        max_length=140,
    )

    def __init__(self, *args, org=None, user=None, **kwargs):
        kwargs["empty_permitted"] = False
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        self.user = user
        licence_field = self.fields["licence"]
        licence_field.queryset = org.licences.all()
        licence_field.label_from_instance = lambda obj: obj.number
        licence_field.initial = instance.licence.number if instance else ""
        self.WIDGET_ERROR_CLASSES["select"] = "govuk-select--error"

    def get_layout(self):
        css_classes = "service-code-widget"
        ptag_kwargs = {}
        if self.errors.get("registration_code"):
            css_classes += " govuk-input--error"
            ptag_kwargs["style"] = "display: none;"

        return Layout(
            TR(
                HiddenField("id"),
                TD(
                    Field(
                        "licence",
                        template="common/forms/table_field.html",
                    ),
                    css_class=(
                        "govuk-table__header "
                        "govuk-!-width-one-third "
                        "licence-dropdown"
                    ),
                ),
                TD(
                    Div(
                        Field(
                            "licence",
                            template=(
                                "site_admin/snippets/"
                                "service_code_exemption/licence_number_text.html"
                            ),
                            **ptag_kwargs,
                        ),
                        Field(
                            "registration_code",
                            template="govuk/widget.html",
                        ),
                        tabindex=0,
                        css_class=css_classes,
                    ),
                    css_class="govuk-table__header govuk-!-width-one-third",
                    css_id="id_service_code-input",
                ),
                TD(
                    Field(
                        "justification",
                        template="govuk/widget.html",
                    ),
                    css_class="govuk-table__header govuk-!-width-one-third",
                ),
                TD(
                    HiddenField("DELETE"),
                    ButtonElement(
                        name="delete",
                        content=_("Delete"),
                        css_class="govuk-button--secondary govuk-!-margin-bottom-0",
                    ),
                    css_class="govuk-table__cell",
                    css_id="id_{{form.prefix}}_delete_td",
                ),
                css_class="govuk-table__row form-container",
                css_id="id_{{form.prefix}}",
            ),
        )

    def clean(self):
        # Override clean to prevent uniqueness validation as this is handled by the
        # formset and will highlight precisely which fields clash
        return self.cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.exempted_by = self.user
        instance.save()
        return instance


class ServiceCodeExceptionsFormsetBase(GOVUKFormMixin, forms.BaseInlineFormSet):
    is_formset = True
    display_formset_template = "site_admin/service_code_exemption_formset/index.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = kwargs.get("queryset")

    @property
    def has_error(self):
        return any(self.errors)

    @property
    def field_has_error(self):
        """
        Returns a dictionary of booleans mapping form fields to a boolean where if any
        form has a field error will be true and false otherwise
        """
        field_errors = {}
        for form in self.forms:
            for field in form.fields:
                original = field_errors.get(field, False)
                field_errors[field] = original or bool(form.errors.get(field, False))

        return field_errors

    @property
    def empty_form(self):
        form = super().empty_form
        form.fields["licence"].widget.attrs.update(
            {"aria-label": "numbers-input-__prefix__"}
        )
        form.fields["registration_code"].widget.attrs.update(
            {"aria-label": "service_code-__prefix__"}
        )
        form.fields["justification"].widget.attrs.update(
            {"aria-label": "exemption-__prefix__"}
        )
        return form

    def get_helper_properties(self):
        props = super().get_helper_properties()
        props["formset_method"] = "post"
        props["disable_csrf"] = False
        props["formset_show_errors"] = True
        return props

    def add_fields(self, form, index):
        """
        Preserve the original licence field, the framework will try
        and make this a hidden foreign key field because licence is
        the parent object but we want the user to be able to select
        this.
        """

        licence_field = form.fields["licence"]
        super().add_fields(form, index)
        form.fields["licence"] = licence_field
        form.fields["licence"].widget.attrs.update(
            {"aria-label": f"numbers-input-{index}"}
        )
        form.fields["registration_code"].widget.attrs.update(
            {"aria-label": f"service_code-{index}"}
        )
        form.fields["justification"].widget.attrs.update(
            {"aria-label": f"exemption-{index}"}
        )

    def set_error_classes(self):
        # Need to override this for the formset.
        # This sets the appropriate CSS error class on each widget on every
        # field with errors.
        for form in self.forms:
            if not form.is_valid():
                form.set_error_classes()

    def save_new(self, form, commit=True):
        """
        Save and return a new model instance for the given form but don't
        rewrite the instance attribute in the form
        """
        return form.save(commit=commit)

    def clean(self):
        if self.has_error:
            # This lazily loads error checking. We want to bail out if there
            # are any failures on the individual forms so they can be fixed before
            # we validate the formset
            return

        service_codes = []
        for form in self.forms:
            data = form.cleaned_data
            service_codes.append((data["licence"].id, data["registration_code"]))
        for index, service_code in enumerate(service_codes):
            if service_codes.count(service_code) >= 2:
                self.forms[index].add_error("registration_code", DUPLICATE_SERVICE_CODE)


ServiceCodeExceptionsFormset = forms.inlineformset_factory(
    Licence,
    ServiceCodeExemption,
    form=ServiceCodeExemptionsForm,
    formset=ServiceCodeExceptionsFormsetBase,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=True,
)
