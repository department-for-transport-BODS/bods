from crispy_forms.layout import Layout
from crispy_forms_govuk.forms import GOVUKForm
from crispy_forms_govuk.layout import ButtonSubmit
from django import forms
from django.utils.translation import ugettext_lazy as _


class CheckboxInputForm(GOVUKForm):
    anonymous = forms.BooleanField(
        initial=False, label="Send this feedback anonymously", required=False
    )

    def get_layout(self):
        return Layout("anonymous", ButtonSubmit(content=_("Submit")))


class CheckboxesForm(GOVUKForm):
    waste = forms.MultipleChoiceField(
        label=_("Which types of waste do you transport?"),
        help_text=_("Choose at least one option."),
        choices=(
            ("carcasses", _("Waste from animal carcasses")),
            ("mines", _("Waste from mines or quarries")),
            ("farm", _("Farm or agricultural waste")),
        ),
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    page_heading_field = "waste"

    def get_layout(self):
        return Layout("waste", ButtonSubmit(content=_("Submit")))


class ErrorSummaryForm(GOVUKForm):
    name = forms.CharField(
        label=_("Full name"),
        required=True,
        error_messages={"required": _("Enter your full name")},
    )

    form_title = _("Your details")

    def get_layout(self):
        return Layout("name", ButtonSubmit(content=_("Submit")))


class FileUploadForm(GOVUKForm):
    file_upload = forms.FileField(label=_("Upload a file"))

    def get_layout(self):
        return Layout("file_upload", ButtonSubmit(content=_("Submit")))


class TextInputForm(GOVUKForm):
    event_name = forms.CharField(label=_("Event name"))

    def get_layout(self):
        return Layout("event_name", ButtonSubmit(content=_("Submit")))


class TextAreaForm(GOVUKForm):
    more_detail = forms.CharField(
        label=_("Can you provide more detail?"),
        help_text=_(
            "Do not include personal or financial information, like your National Insurance number or credit card "
            "details. "
        ),
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    def get_layout(self):
        return Layout("more_detail", ButtonSubmit(content=_("Submit")))
