from crispy_forms.layout import ButtonHolder, Field, Layout
from transit_odp.crispy_forms_govuk.forms import GOVUKFormMixin, GOVUKModelForm
from transit_odp.crispy_forms_govuk.layout import (
    ButtonElement,
    ButtonSubmit,
    LinkButton,
)
from transit_odp.crispy_forms_govuk.layout.fields import (
    CheckboxSingleField,
    HiddenField,
)
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from transit_odp.common.layout import TD, TR, InlineFormset
from transit_odp.organisation.constants import (
    PSV_LICENCE_ERROR_HINT_MESSAGE,
    PSV_LICENCE_ERROR_MESSAGE,
)
from transit_odp.organisation.models import Licence, OperatorCode, Organisation


class BaseFormsetForm(GOVUKFormMixin, forms.ModelForm):
    is_formset = True  # necessary to ensure inner form tags are not rendered
    field = None
    delete_script = """
        document.getElementById('id_{{form.prefix}}-DELETE').value='on';
        document.getElementById('id_{{form.prefix}}').style.display = 'none';
    """

    def get_layout(self):
        # Note when using an Inline/ModelFormset we must explicitly render
        # form.id in the layout. This renders a hidden input with a value of the
        # bound instance's pk which ensures the forms are mapped to the instances.
        return Layout(
            HiddenField("id"),
            TR(
                TD(
                    Field(self.field, template="common/forms/table_field.html"),
                    css_class="govuk-table__header govuk-!-width-one-third",
                ),
                TD(
                    # This field is added dynamically by the formset, we don't want
                    # to render it visually
                    HiddenField("DELETE"),
                    ButtonElement(
                        name="delete",
                        content=_("Delete"),
                        css_class="govuk-button--secondary govuk-!-margin-bottom-0",
                        # TODO do a better job of it than this...
                        onclick=self.delete_script,
                    ),
                    css_class="govuk-table__cell",
                    css_id="id_{{form.prefix}}_delete_td",
                ),
                css_class="govuk-table__row",
                css_id="id_{{form.prefix}}",
            ),
        )


class NOCForm(BaseFormsetForm):
    field = "noc"

    noc = forms.CharField(
        label="National Operator Code",
        widget=forms.TextInput(attrs={"aria-label": "nocs-input-0"}),
        error_messages={"required": "National Operator Code cannot be blank"},
    )

    class Meta:
        model = OperatorCode
        fields = ("noc",)


class PSVForm(BaseFormsetForm):
    field = "number"
    delete_script = """
         // send out the input event that input is empty
        const licenceId ='id_{{form.prefix}}';
        const input = document.getElementById(licenceId + '-number');
        input.dispatchEvent(new InputEvent('input', {data: licenceId}));
    """

    number = forms.CharField(
        label="PSV Licence number",
        widget=forms.TextInput(attrs={"aria-label": "number-input-0"}),
        required=False,
        validators=(
            RegexValidator(
                regex=r"[a-zA-Z]{2}\d{7}", message=PSV_LICENCE_ERROR_MESSAGE
            ),
        ),
    )

    def clean_number(self, *args, **kwargs):
        """
        Cleans the number field.
        """

        # This is an extra check so that it is impossible to update
        # a current licence with "" see BODP-4241
        number = self.cleaned_data["number"]
        if number == "":
            raise ValidationError(PSV_LICENCE_ERROR_MESSAGE)
        return number

    class Meta:
        model = Licence
        fields = ("number",)


class BaseInlineFormset(GOVUKFormMixin, forms.BaseInlineFormSet):
    is_formset = True  # necessary to ensure inner form tags are not rendered
    display_formset_template = None

    def set_error_classes(self):
        # Need to override this for the formset.
        # This sets the appropriate CSS error class on each widget on every
        # field with errors.
        for form in self.forms:
            if not form.is_valid():
                form.set_error_classes()

    @property
    def has_error(self):
        for error in self.errors:
            if error:
                return True

        return False

    def full_clean(self):
        super().full_clean()

        # NOTE - this doesn't seem to want to work, putting this logic in the JS!
        # TODO - would probably be better defined in Python
        # The invalid form will be rerendered with the previous state. We need to
        # reset the DELETE inputs since there is no way for the user to untick the
        # input once checked


class BaseInlineNOCFormset(BaseInlineFormset):
    display_formset_template = (
        "organisation/organisation_profile_form/noc_table_formset.html"
    )

    @property
    def empty_form(self):
        form = super().empty_form
        form.fields["noc"].widget.attrs.update({"aria-label": "nocs-input-__prefix__"})
        return form

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if index is not None:
            form.fields["noc"].widget.attrs.update(
                {"aria-label": f"nocs-input-{index}"}
            )

    def non_form_errors(self):
        errors = super().non_form_errors()
        for error in errors.data:
            # Cant find a better way of changing this error message.
            # maybe in the next version of django the error_messages kwarg will work
            if error.code == "too_few_forms":
                error.message = (
                    f"Please submit {self.min_num} or more National Operator Codes"
                )
        return errors


class BaseInlinePSVFormset(BaseInlineFormset):
    display_formset_template = (
        "organisation/organisation_profile_form/psv_table_formset.html"
    )

    @property
    def empty_form(self):
        form = super().empty_form
        form.fields["number"].widget.attrs.update(
            {"aria-label": "numbers-input-__prefix__"}
        )
        return form

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if index is not None:
            form.fields["number"].widget.attrs.update(
                {"aria-label": f"numbers-input-{index}"}
            )

    @property
    def validation_error_hint(self):
        return PSV_LICENCE_ERROR_HINT_MESSAGE


NOCFormset = forms.inlineformset_factory(
    Organisation,
    OperatorCode,
    form=NOCForm,
    formset=BaseInlineNOCFormset,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

PSVFormset = forms.inlineformset_factory(
    Organisation,
    Licence,
    form=PSVForm,
    formset=BaseInlinePSVFormset,
    extra=0,
    can_delete=True,
    min_num=0,
    validate_min=True,
)


class OrganisationProfileForm(GOVUKModelForm):
    errors_template = "organisation/organisation_profile_form/errors.html"

    class Meta:
        model = Organisation
        fields = ["short_name", "licence_required"]
        labels = {
            "short_name": _("Shortname"),
        }

    def __init__(
        self, data=None, files=None, instance=None, cancel_url=None, *args, **kwargs
    ):
        super().__init__(data=data, files=files, instance=instance, *args, **kwargs)
        self.cancel_url = cancel_url

        # Create a nested formset
        self.nested_noc = NOCFormset(
            instance=instance,
            data=data if self.is_bound else None,
            files=files if self.is_bound else None,
        )

        self.nested_psv = PSVFormset(
            instance=instance,
            data=data if self.is_bound else None,
            files=files if self.is_bound else None,
        )

        short_name = self.fields["short_name"]
        short_name.widget.attrs.update({"class": "govuk-!-width-two-thirds"})

        licence_required = self.fields["licence_required"]
        licence_required.widget = forms.CheckboxInput()
        licence_required.label = "I do not have a PSV Licence number"

    def get_helper_properties(self):
        props = super().get_helper_properties()
        # Add nested formset to helper properties. This will expose it in the context
        props.update({"nested_noc": self.nested_noc, "nested_psv": self.nested_psv})
        return props

    def has_licence_numbers(self):
        if self.instance.licences.exists():
            # Case 1: There are licences in the database (and will therefore be initial
            # inputs prefilled with licence numbers).
            return True
        total_forms = int(self.data.get("licences-TOTAL_FORMS", "0"))
        for index in range(total_forms):
            # Case 2: There may be licences in the inputs that havent been submitted
            # yet. Iterate through until we find one
            if self.data.get(f"licences-{index}-number", False):
                return True

        return False

    def get_layout(self):
        if self.has_licence_numbers():
            checkbox = CheckboxSingleField(
                "licence_required",
                small_boxes=True,
                disabled=True,
            )
        else:
            checkbox = CheckboxSingleField(
                "licence_required",
                small_boxes=True,
            )

        return Layout(
            Field(
                "short_name", wrapper_class="govuk-form-group govuk-!-margin-bottom-4"
            ),
            InlineFormset("nested_noc"),
            InlineFormset("nested_psv"),
            checkbox,
            ButtonHolder(
                ButtonSubmit(name="submit", content=_("Save")),
                LinkButton(url=self.cancel_url, content="Cancel"),
            ),
        )

    def clean_licence_required(self):
        return not self.cleaned_data["licence_required"]

    def is_valid(self):
        """
        Also validate the nested formsets.
        """
        is_valid = super().is_valid()
        noc = self.nested_noc.is_valid()
        psv = self.nested_psv.is_valid()
        return all((is_valid, noc, psv))

    def clean(self):
        # At this point "licence required" is inverted from db
        org_data = self.cleaned_data
        if [error for error in self.nested_psv.errors if error != {}]:
            return org_data

        new_or_existing = []
        for data in self.nested_psv.cleaned_data:
            # filter out deleted or empty forms
            if data == {} or data["DELETE"]:
                continue
            new_or_existing.append(data)

        if len(new_or_existing) > 0 and not org_data["licence_required"]:
            self.add_error(
                field="licence_required",
                error=(
                    'Untick "I do not have a PSV licence number" '
                    "checkbox to add licences"
                ),
            )

        return org_data

    def save(self, commit=True):
        inst = super().save(commit=commit)
        self.nested_noc.save(commit=commit)
        self.nested_psv.save(commit=commit)
        return inst
