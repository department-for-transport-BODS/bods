from collections import Counter
from string import ascii_uppercase

from crispy_forms.layout import Layout
from transit_odp.crispy_forms_govuk.forms import GOVUKForm
from transit_odp.crispy_forms_govuk.layout import ButtonSubmit
from transit_odp.crispy_forms_govuk.layout.fields import (
    CheckboxMultipleField,
    LegendSize,
)
from django import forms
from django.contrib import auth
from django.forms import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _
from invitations.utils import get_invitation_model

from transit_odp.organisation.constants import (
    ORG_ACTIVE,
    ORG_INACTIVE,
    ORG_NOT_YET_INVITED,
    ORG_PENDING_INVITE,
)

User = auth.get_user_model()
Invitation = get_invitation_model()

LETTER_CHOICES = [("0-9", "0 - 9")] + [(letter, letter) for letter in ascii_uppercase]
STATUS_CHOICES = (
    ("", "All statuses"),
    (ORG_ACTIVE, ORG_ACTIVE),
    (ORG_INACTIVE, ORG_INACTIVE),
    (ORG_PENDING_INVITE, ORG_PENDING_INVITE),
    (ORG_NOT_YET_INVITED, ORG_NOT_YET_INVITED),
)
CHECKBOX_FIELD_KEY = "letters"


class CheckboxFilterForm(GOVUKForm):
    form_method = "get"
    letters = forms.MultipleChoiceField(
        choices=LETTER_CHOICES, widget=CheckboxSelectMultiple(), required=False
    )
    form_label = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields[CHECKBOX_FIELD_KEY]
        if self.form_label is not None:
            field.label = self.form_label

        qs = self.get_queryset()
        field.first_letter_count = Counter(qs.values_list("first_letter", flat=True))
        digits = [str(i) for i in range(10)]
        digits_count = qs.filter(first_letter__in=digits).count()
        field.first_letter_count["0 - 9"] = digits_count

    def get_queryset(self):
        # Implement this in the derived class
        raise NotImplementedError()

    def get_layout(self):
        template = "common/forms/checkbox_filter_field.html"

        return Layout(
            CheckboxMultipleField(
                CHECKBOX_FIELD_KEY, legend_size=LegendSize.s, template=template
            ),
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )

    def clean_letters(self):
        letters = self.cleaned_data[CHECKBOX_FIELD_KEY]
        if not letters:
            return []

        if letters[0] == "0-9":
            letters.pop(0)
            return letters + list(map(str, range(10)))

        return letters
