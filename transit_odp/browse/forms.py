import datetime

from crispy_forms.layout import Field, Layout
from crispy_forms_govuk.forms import GOVUKForm
from crispy_forms_govuk.layout import ButtonSubmit
from dateutil.parser import parse
from django import forms
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _
from django_filters.constants import EMPTY_VALUES

from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.models import Organisation


class TimetableSearchFilterForm(GOVUKForm):
    form_method = "get"
    form_tag = False

    area = forms.ModelChoiceField(
        queryset=AdminArea.objects.all(),
        required=False,
        label=_("Geographical area"),
        empty_label="All geographical areas",
    )

    organisation = forms.ModelChoiceField(
        queryset=Organisation.objects.exclude(is_active=False),
        required=False,
        label=_("Publisher"),
        empty_label="All publishers",
    )

    status = forms.ChoiceField(
        choices=(
            ("", "All statuses"),
            (FeedStatus.live.value, "Published"),
            (FeedStatus.expiring.value, "Soon to expire"),
            (FeedStatus.expired.value, "Expired"),
            (FeedStatus.inactive.value, "Inactive"),
        ),
        required=False,
    )
    start = forms.CharField(
        required=False,
        label=_("Timetable start date after"),
        help_text="For example, 2005 or 21/11/2014",
        error_messages={"invalid": _("Timetable start date not in correct format")},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change field labels
        self.fields["area"].label_from_instance = lambda obj: obj.name
        self.fields["organisation"].label_from_instance = lambda obj: obj.name

    def get_layout(self):
        return Layout(
            Field("area", css_class="govuk-!-width-full"),
            Field("organisation", css_class="govuk-!-width-full"),
            Field("status", css_class="govuk-!-width-full"),
            Field("start", css_class="govuk-!-width-full"),
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )

    def clean_start(self):
        time_string = self.cleaned_data["start"]

        if time_string in EMPTY_VALUES:
            return time_string

        current_year = localtime().year
        default_time = datetime.datetime(current_year, 1, 1)

        try:
            return parse(time_string, default=default_time, dayfirst=True)
        except ValueError as e:
            raise forms.ValidationError(
                self.fields["start"].error_messages["invalid"]
            ) from e


class AVLSearchFilterForm(GOVUKForm):
    form_method = "get"
    form_tag = False

    organisation = forms.ModelChoiceField(
        queryset=Organisation.objects.exclude(is_active=False),
        required=False,
        label=_("Publisher"),
        empty_label="All publishers",
    )

    status = forms.ChoiceField(
        choices=(
            ("", "All statuses"),
            (FeedStatus.live.value, "Published"),
            (FeedStatus.error.value, "Error"),
            (FeedStatus.inactive.value, "Deactivated"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change field labels
        self.fields["organisation"].label_from_instance = lambda obj: obj.name

    def get_layout(self):
        return Layout(
            Field("organisation", css_class="govuk-!-width-full"),
            Field("status", css_class="govuk-!-width-full"),
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )


class FaresSearchFilterForm(GOVUKForm):
    form_method = "get"
    form_tag = False

    area = forms.ModelChoiceField(
        queryset=AdminArea.objects.all(),
        required=False,
        label=_("Geographical area"),
        empty_label="All geographical areas",
    )

    organisation = forms.ModelChoiceField(
        queryset=Organisation.objects.exclude(is_active=False),
        required=False,
        label=_("Publisher"),
        empty_label="All publishers",
    )

    status = forms.ChoiceField(
        choices=(
            ("", "All statuses"),
            (FeedStatus.live.value, "Published"),
            (FeedStatus.expiring.value, "Soon to expire"),
            (FeedStatus.expired.value, "Expired"),
            (FeedStatus.inactive.value, "Inactive"),
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change field labels
        self.fields["area"].label_from_instance = lambda obj: obj.name
        self.fields["organisation"].label_from_instance = lambda obj: obj.name

    def get_layout(self):
        return Layout(
            Field("area", css_class="govuk-!-width-full"),
            Field("organisation", css_class="govuk-!-width-full"),
            Field("status", css_class="govuk-!-width-full"),
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )


class UserFeedbackForm(GOVUKForm):
    feedback = forms.CharField(
        label="Please provide feedback.",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
        error_messages={"required": _("Enter feedback in the box below")},
    )
    anonymous = forms.BooleanField(
        initial=False, label="Send this feedback anonymously", required=False
    )

    form_title = "Provide feedback"

    def get_layout(self):
        return Layout("feedback", "anonymous", ButtonSubmit(content=_("Submit")))
