from crispy_forms.layout import HTML, Field, Layout
from crispy_forms_govuk.forms import GOVUKForm, GOVUKFormMixin, GOVUKModelForm
from crispy_forms_govuk.layout import ButtonElement, ButtonSubmit
from crispy_forms_govuk.layout.fields import HiddenField
from django import forms
from django.utils.translation import gettext_lazy as _
from sandbox.demo import models as demo_models
from sandbox.demo.layout import TD, TR


class SignupForm(GOVUKForm):
    form_title = "Create an account"

    email = forms.EmailField(
        label=_("Email address"),
        max_length=150,
        error_messages={
            "required": _("Email should not be empty"),
            "invalid": _(
                "Enter an email address in the right format, like name@example.com"
            ),
        },
    )
    password1 = forms.CharField(
        label=_("Password"),
        max_length=32,
        min_length=8,
        widget=forms.PasswordInput,
        help_text=_(
            "Password must be 8 to 32 characters in length with at least one number and one letter"
        ),
        error_messages={
            "required": _("Enter a password"),
            "invalid": _(
                "Password must be 8 to 32 characters in length with at least one number and one letter"
            ),
        },
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput,
        error_messages={
            "required": _("Confirm your password"),
            "invalid": _(
                "Password must be 8 to 32 characters in length with at least one number and one letter"
            ),
        },
    )

    def get_layout(self):
        return Layout(
            HTML(
                '<p class="govuk-body-l">Enter your details to create an account.</p>'
            ),
            "email",
            "password1",
            "password2",
            ButtonSubmit("submit", "submit", content=_("Create an account")),
        )

    def clean(self):
        cleaned_data = super().clean()
        if (
            "password1" in self.cleaned_data
            and "password2" in self.cleaned_data
            and cleaned_data["password1"] != cleaned_data["password2"]
        ):
            self.add_error("password2", _("You must type the same password each time."))
        return cleaned_data


class PostCodeQuestionPageForm(GOVUKForm):
    postcode = forms.CharField(
        label=_("What is your home postcode?"),
        widget=forms.TextInput(
            attrs={"id": "postcode", "class": "govuk-input--width-10"}
        ),
        required=True,
    )

    page_heading_field = "postcode"

    def get_layout(self):
        return Layout("postcode", ButtonSubmit(content=_("Continue")))


class RadiosQuestionPage(GOVUKForm):
    country = forms.ChoiceField(
        label=_("Where do you live?"),
        choices=(
            ("england", _("England")),
            ("scotland", _("Scotland")),
            ("wales", _("Wales")),
            ("northern-ireland", _("Northern Ireland")),
        ),
        required=True,
        widget=forms.RadioSelect(),
    )

    page_heading_field = "country"

    def get_layout(self):
        return Layout("country", ButtonSubmit(content=_("Continue")))


class NOCForm(GOVUKFormMixin, forms.ModelForm):
    is_formset = True  # necessary to ensure inner form tags are not rendered

    noc = forms.CharField(label="National Operator Code")

    class Meta:
        fields = ("noc",)

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def get_layout(self):
        # Note when using an Inline/ModelFormset we must explicitly render form.id in the layout. This renders a hidden
        # input with a value of the bound instance's pk which ensures the forms are mapped to the instances.
        return Layout(
            HiddenField("id"),
            TR(
                TD(
                    Field("noc", template="demo/forms/table_field.html"),
                    css_class="govuk-table__header govuk-!-width-one-third",
                ),
                TD(
                    # This field is added dynamically by the formset, we don't want to render it visually
                    HiddenField("DELETE"),
                    ButtonElement(
                        name="delete",
                        content=_("Delete"),
                        css_class="govuk-button--secondary govuk-!-margin-bottom-0",
                        # Do a better job of it than this...
                        onclick="document.getElementById('id_{{form.prefix}}-DELETE').value = 'on'; document.getElementById('id_{{form.prefix}}').style.display = 'none';",
                    ),
                    css_class="govuk-table__cell",
                ),
                css_class="govuk-table__row",
                css_id="id_{{form.prefix}}",
            ),
        )


class BaseInlineNOCFormset(GOVUKFormMixin, forms.BaseInlineFormSet):
    form_title = "Edit national operator codes"
    display_formset_template = "demo/forms/table_formset.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.helper.add_input(ButtonSubmit(name="submit", content=_("Submit")))

    def set_error_classes(self):
        # Need to override this for the formset.
        # This sets the appropriate CSS error class on each widget on every field with errors.
        for form in self.forms:
            if not form.is_valid():
                form.set_error_classes()


NOCFormset = forms.inlineformset_factory(
    demo_models.Organisation,
    demo_models.NOC,
    form=NOCForm,
    formset=BaseInlineNOCFormset,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
