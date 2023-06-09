from crispy_forms.layout import Field, Layout
from crispy_forms_govuk.forms import GOVUKForm, GOVUKModelForm
from crispy_forms_govuk.layout import ButtonSubmit
from django import forms
from django.forms.widgets import NumberInput
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from waffle import flag_is_active

from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.models import ConsumerFeedback, Organisation


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
            (FeedStatus.inactive.value, "Inactive"),
        ),
        required=False,
    )

    is_pti_compliant = forms.NullBooleanField(
        required=False,
        label=_("BODS compliance"),
    )

    start = forms.DateTimeField(
        required=False,
        label=_("Timetable start date after"),
        help_text="For example: 21/11/2014",
        error_messages={"invalid": _("Timetable start date not in correct format")},
        widget=NumberInput(attrs={"type": "date"}),
    )

    published_at = forms.DateTimeField(
        required=False,
        label=_("Timetable last updated after"),
        help_text="For example: 21/11/2014",
        error_messages={"invalid": _("Timetable last updated not in correct format")},
        widget=NumberInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change field labels
        self.fields["area"].label_from_instance = lambda obj: obj.name
        self.fields["organisation"].label_from_instance = lambda obj: obj.name
        is_pti_compliant = self.fields["is_pti_compliant"]
        is_pti_compliant.label_from_instance = (
            lambda obj: "PTI compliant" if obj else "Not PTI compliant"
        )
        # Use a boolean field and change the widget to get type conversion for free
        is_pti_compliant.widget = forms.Select(
            choices=(
                (None, "All statuses"),
                (True, "Compliant"),
                (False, "Non compliant"),
            )
        )
        self.fields["is_pti_compliant"].label += mark_safe(
            render_to_string(
                "browse/snippets/help_modals/timetables_pti_compliance.html"
            )
        )

    def get_layout(self):
        return Layout(
            Field("area", css_class="govuk-!-width-full"),
            Field("organisation", css_class="govuk-!-width-full"),
            Field("status", css_class="govuk-!-width-full"),
            Field("is_pti_compliant", css_class="govuk-!-width-full"),
            Field("start"),
            Field("published_at"),
            ButtonSubmit("submitform", "submit", content=_("Apply filter")),
        )


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
            (FeedStatus.inactive.value, "Inactive"),
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
            (FeedStatus.inactive.value, "Inactive"),
        ),
        required=False,
    )

    is_fares_compliant = forms.NullBooleanField(
        required=False,
        label=_("BODS compliance"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change field labels
        self.fields["area"].label_from_instance = lambda obj: obj.name
        self.fields["organisation"].label_from_instance = lambda obj: obj.name
        self.is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
        if self.is_fares_validator_active:
            is_fares_compliant = self.fields["is_fares_compliant"]
            is_fares_compliant.label_from_instance = (
                lambda obj: "BODS compliant" if obj else "Not BODS compliant"
            )
            is_fares_compliant.widget = forms.Select(
                choices=(
                    (None, "All statuses"),
                    (True, "Compliant"),
                    (False, "Non compliant"),
                )
            )

    def get_layout(self):
        if self.is_fares_validator_active:
            return Layout(
                Field("area", css_class="govuk-!-width-full"),
                Field("organisation", css_class="govuk-!-width-full"),
                Field("status", css_class="govuk-!-width-full"),
                Field("is_fares_compliant", css_class="govuk-!-width-full"),
                ButtonSubmit("submitform", "submit", content=_("Apply filter")),
            )
        else:
            return Layout(
                Field("area", css_class="govuk-!-width-full"),
                Field("organisation", css_class="govuk-!-width-full"),
                Field("status", css_class="govuk-!-width-full"),
                ButtonSubmit("submitform", "submit", content=_("Apply filter")),
            )


class ConsumerFeedbackForm(GOVUKModelForm):
    class Meta:
        model = ConsumerFeedback
        fields = (
            "feedback",
            "consumer_id",
            "dataset_id",
            "organisation_id",
        )

    feedback = forms.CharField(
        label="What best describes the issue you are experiencing?*",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=True,
        error_messages={"required": _("Enter feedback in the box below")},
    )
    consumer_id = forms.IntegerField(
        show_hidden_initial=True, disabled=True, required=False
    )
    dataset_id = forms.IntegerField(
        show_hidden_initial=True, disabled=True, required=False
    )
    organisation_id = forms.IntegerField(
        show_hidden_initial=True, disabled=True, required=False
    )

    anonymous = forms.BooleanField(
        initial=False, label="Send this feedback anonymously", required=False
    )

    def get_layout(self):
        return Layout(
            "feedback",
            "anonymous",
            ButtonSubmit(content=_("Send")),
        )

    def has_changed(self):
        # We always want to create from initial
        return True

    def clean(self):
        data = super().clean()
        if data["anonymous"]:
            data["consumer_id"] = None

        return data

    def save(self, commit=True):
        # need to force the initial data onto the new object because they only get
        # added if they are in the http form on the frontend. We dont want the
        # user to be able to set the user id or dataset id so they are hidden and
        # disabled
        instance = super().save(commit=False)
        instance.dataset_id = self.cleaned_data["dataset_id"]
        instance.consumer_id = self.cleaned_data["consumer_id"]
        instance.organisation_id = self.cleaned_data["organisation_id"]
        instance.save()
        return instance
