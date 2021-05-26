from crispy_forms.layout import ButtonHolder, Field, Layout
from crispy_forms_govuk.forms import GOVUKFormMixin, GOVUKModelForm
from crispy_forms_govuk.layout import ButtonElement, ButtonSubmit, LinkButton
from crispy_forms_govuk.layout.fields import HiddenField
from django import forms
from django.utils.translation import gettext_lazy as _

from transit_odp.common.layout import TD, TR, InlineFormset
from transit_odp.organisation.models import OperatorCode, Organisation


class NOCForm(GOVUKFormMixin, forms.ModelForm):
    is_formset = True  # necessary to ensure inner form tags are not rendered

    noc = forms.CharField(
        label="National Operator Code",
        widget=forms.TextInput(attrs={"aria-label": "nocs-input-0"}),
    )

    class Meta:
        model = OperatorCode
        fields = ("noc",)

    def get_layout(self):
        # Note when using an Inline/ModelFormset we must explicitly render
        # form.id in the layout. This renders a hidden input with a value of the
        # bound instance's pk which ensures the forms are mapped to the instances.
        return Layout(
            HiddenField("id"),
            TR(
                TD(
                    Field("noc", template="common/forms/table_field.html"),
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
                        onclick=(
                            "document.getElementById('id_{{form.prefix}}-DELETE')."
                            "value='on'; "
                            "document.getElementById('id_{{form.prefix}}')."
                            "style.display = 'none';"
                        ),
                    ),
                    css_class="govuk-table__cell",
                ),
                css_class="govuk-table__row",
                css_id="id_{{form.prefix}}",
            ),
        )


class BaseInlineNOCFormset(GOVUKFormMixin, forms.BaseInlineFormSet):
    is_formset = True  # necessary to ensure inner form tags are not rendered
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

    def set_error_classes(self):
        # Need to override this for the formset.
        # This sets the appropriate CSS error class on each widget on every
        # field with errors.
        for form in self.forms:
            if not form.is_valid():
                form.set_error_classes()

    def full_clean(self):
        super().full_clean()

        # NOTE - this doesn't seem to want to work, putting this logic in the JS!
        # TODO - would probably be better defined in Python
        # The invalid form will be rerendered with the previous state. We need to
        # reset the DELETE inputs since there is no way for the user to untick the
        # input once checked


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


class OrganisationProfileForm(GOVUKModelForm):
    errors_template = "organisation/organisation_profile_form/errors.html"

    class Meta:
        model = Organisation
        fields = ["short_name"]
        labels = {
            "short_name": _("Shortname"),
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

        short_name = self.fields["short_name"]
        short_name.widget.attrs.update({"class": "govuk-!-width-two-thirds"})

    def get_helper_properties(self):
        props = super().get_helper_properties()
        # Add nested formset to helper properties. This will expose it in the context
        props.update({"nested": self.nested})
        return props

    def get_layout(self):
        return Layout(
            Field(
                "short_name", wrapper_class="govuk-form-group govuk-!-margin-bottom-4"
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
        inst = super().save(commit=commit)
        self.nested.save(commit=commit)
        return inst
