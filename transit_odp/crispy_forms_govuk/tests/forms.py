from crispy_forms_govuk.forms import GOVUKForm
from django import forms


class EmptyForm(forms.Form):
    """An empty form."""

    def save(self, commit=True):
        return


class BasicForm(forms.Form):
    """Basic form with a single CharField field."""

    event = forms.CharField(label="Event name", max_length=250, required=True)

    def save(self, commit=True):
        return


class CheckboxForm(forms.Form):
    checkbox = forms.BooleanField(
        label="Would you like to receive weekly our newsletter?",
        help_text="Periodic news, announcements and product updates",
    )

    def save(self, commit=True):
        return


class FormWithErrorFrom(GOVUKForm):
    event = forms.CharField(label="Event name", max_length=250, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
