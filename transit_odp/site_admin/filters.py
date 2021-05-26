import django_filters as filters
from django.contrib.auth import get_user_model
from django.forms import Select

from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.models import DatasetRevision, Organisation
from transit_odp.site_admin.forms import AVLSearchFilterForm, TimetableSearchFilterForm

User = get_user_model()


class OrganisationFilter(filters.FilterSet):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("pending", "Pending Invite"),
    )
    OPERATOR_CHOICES = (
        ("a-f", "A - F"),
        ("g-l", "G - L"),
        ("m-r", "M - R"),
        ("s-z", "S - Z"),
    )
    status = filters.ChoiceFilter(
        label="Status",
        empty_label="All statuses",
        choices=STATUS_CHOICES,
        widget=Select(attrs={"class": "govuk-!-width-full govuk-select"}),
    )
    operators = filters.ChoiceFilter(
        label="Operators",
        empty_label="All operators",
        choices=OPERATOR_CHOICES,
        widget=Select(attrs={"class": "govuk-!-width-full govuk-select"}),
        method="filter_by_name",
    )

    def filter_by_name(self, queryset, name, value):
        lower, upper = value.split("-")
        return queryset.filter(first_letter__gte=lower, first_letter__lte=upper)

    class Meta:
        model = Organisation
        fields = ["operators", "status"]


class ConsumerFilter(filters.FilterSet):
    EMAIL_CHOICES = (
        ("a-f", "A - F"),
        ("g-l", "G - L"),
        ("m-r", "M - R"),
        ("s-z", "S - Z"),
    )
    email = filters.ChoiceFilter(
        label="Email",
        empty_label="All emails",
        choices=EMAIL_CHOICES,
        widget=Select(attrs={"class": "govuk-!-width-full govuk-select"}),
        method="filter_by_email",
    )

    def filter_by_email(self, queryset, name, value):
        lower, upper = value.split("-")
        return queryset.filter(
            email_first_letter__gte=lower, email_first_letter__lte=upper
        )

    class Meta:
        model = User
        fields = ["email"]


class BaseDatasetSearchFilter(filters.FilterSet):
    status = filters.ChoiceFilter(
        choices=DatasetRevision.STATUS_CHOICES + ((FeedStatus.live.value, "Published"),)
    )

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form


class TimetableSearchFilter(BaseDatasetSearchFilter):
    class Meta:
        form = TimetableSearchFilterForm
        fields = ["status"]


class AVLSearchFilter(BaseDatasetSearchFilter):
    class Meta:
        form = AVLSearchFilterForm
        fields = ["status"]
