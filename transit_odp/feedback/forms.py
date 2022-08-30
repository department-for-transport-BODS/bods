from crispy_forms.layout import HTML, Layout
from crispy_forms_govuk.forms import GOVUKModelForm
from crispy_forms_govuk.layout.buttons import ButtonSubmit
from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from .models import Feedback, SatisfactionRating

SEND_FEEDBACK_BUTTON = ButtonSubmit("submit", "submit", content=_("Send Feedback"))
MAX_LENGTH_COMMENT = 1200


class CustomMaxLengthValidator(MaxLengthValidator):
    def clean(self, chars):
        counter = 0
        for char in chars:
            if char != "\r":
                counter += 1

        return counter


class GlobalFeedbackForm(GOVUKModelForm):
    class Meta:
        model = Feedback
        fields = (
            "satisfaction_rating",
            "comment",
            "page_url",
        )

    form_title = _("Give feedback on Bus Open Data Service")
    satisfaction_rating = forms.ChoiceField(
        label="",
        choices=[(real, label) for real, label in SatisfactionRating.choices],
        widget=forms.RadioSelect(attrs={"id": "feedback_type"}),
        initial=2,
    )
    comment = forms.CharField(
        label="",
        validators=[CustomMaxLengthValidator(MAX_LENGTH_COMMENT)],
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "maxlength": MAX_LENGTH_COMMENT,
            }
        ),
        help_text=_(
            "Do not include any personal or financial "
            "information such as your National Insurance "
            "or credit card numbers."
        ),
        strip=False,
        required=False,
    )
    page_url = forms.CharField(label="", required=False, widget=forms.HiddenInput())

    def __init__(self, *args, url=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        page_url = self.fields["page_url"]
        page_url.initial = self.url
        page_url.widget.attrs.update({"readonly": True})

    def get_layout(self):
        return Layout(
            HTML(
                '<p class="govuk-label govuk-!-font-weight-bold">'
                "How did you find Bus Open Data Service today?</p>"
            ),
            "satisfaction_rating",
            HTML(
                '<p class="govuk-label govuk-!-font-weight-bold">'
                "How could we improve this service? (optional)</p>"
            ),
            "comment",
            HTML(
                '<span class="govuk-hint">You have '
                '<span id="comment_char_count"></span>'
                " characters remaining"
                "</span>"
            ),
            "page_url",
            SEND_FEEDBACK_BUTTON,
        )

    def clean_page_url(self):
        return self.url

    def clean_comment(self):
        return self.cleaned_data["comment"].replace("\r", "")
