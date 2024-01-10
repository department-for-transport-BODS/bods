from string import ascii_uppercase

from crispy_forms.layout import Field, Layout
from transit_odp.crispy_forms_govuk.forms import GOVUKForm
from transit_odp.crispy_forms_govuk.layout import ButtonSubmit
from django import forms
from django.contrib import auth
from django.utils.translation import gettext_lazy as _
from invitations.utils import get_invitation_model

from transit_odp.organisation.constants import (
    ORG_ACTIVE,
    ORG_INACTIVE,
    ORG_NOT_YET_INVITED,
    ORG_PENDING_INVITE,
    FeedStatus,
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


class BaseDatasetSearchFilterForm(GOVUKForm):
    form_method = "get"
    form_tag = False

    status = forms.ChoiceField(
        choices=(
            ("", "All statuses"),
            (FeedStatus.live.value, "Published"),
            (FeedStatus.success.value, "Draft"),
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
            (FeedStatus.error.value, "No vehicle activity"),
            (FeedStatus.inactive.value, "Inactive"),
            (FeedStatus.success.value, "Draft"),
        ),
        required=False,
    )
