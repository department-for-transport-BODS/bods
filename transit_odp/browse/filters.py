import django_filters as filters
from django.db.models import Q

from transit_odp.avl.constants import (
    AWAITING_REVIEW,
    COMPLIANT,
    MORE_DATA_NEEDED,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
    UNDERGOING,
)
from transit_odp.browse.forms import (
    AVLSearchFilterForm,
    FaresSearchFilterForm,
    TimetableSearchFilterForm,
)
from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import SEARCH_STATUS_CHOICES, FeedStatus
from transit_odp.organisation.models import DatasetRevision, Organisation


class TimetableSearchFilter(filters.FilterSet):
    area = filters.ModelChoiceFilter(
        field_name="admin_areas",
        queryset=AdminArea.objects.all(),
        method="admin_areas_filter",
    )
    organisation = filters.ModelChoiceFilter(
        queryset=Organisation.objects.exclude(is_active=False)
    )

    status = filters.ChoiceFilter(choices=SEARCH_STATUS_CHOICES)
    start = filters.DateTimeFilter(field_name="first_service_start", lookup_expr="gte")
    published_at = filters.DateTimeFilter(field_name="published_at", lookup_expr="gte")

    is_pti_compliant = filters.BooleanFilter()

    class Meta:
        form = TimetableSearchFilterForm

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form

    def admin_areas_filter(self, queryset, name, value):
        # admin_area_names have been annotated onto the dataset

        if value:
            value = value.name
            queryset = queryset.filter(Q(admin_area_names__contains=value))
        return queryset


class AVLSearchFilter(filters.FilterSet):
    organisation = filters.ModelChoiceFilter(
        queryset=Organisation.objects.exclude(is_active=False)
    )

    status = filters.ChoiceFilter(
        choices=(
            ("", "All statuses"),
            (FeedStatus.live.value, "Published"),
            (FeedStatus.error.value, "No vehicle activity"),
            (FeedStatus.inactive.value, "Inactive"),
        ),
    )

    avl_compliance_status_cached = filters.ChoiceFilter(
        choices=(
            (UNDERGOING, UNDERGOING),
            (PARTIALLY_COMPLIANT, PARTIALLY_COMPLIANT),
            (MORE_DATA_NEEDED, MORE_DATA_NEEDED),
            (AWAITING_REVIEW, AWAITING_REVIEW),
            (COMPLIANT, COMPLIANT),
            (NON_COMPLIANT, NON_COMPLIANT),
        )
    )

    class Meta:
        form = AVLSearchFilterForm

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form


class FaresSearchFilter(filters.FilterSet):
    area = filters.ModelChoiceFilter(
        field_name="admin_areas",
        queryset=AdminArea.objects.all(),
        method="admin_areas_filter",
    )
    organisation = filters.ModelChoiceFilter(
        queryset=Organisation.objects.exclude(is_active=False)
    )

    status = filters.ChoiceFilter(choices=DatasetRevision.STATUS_CHOICES)

    is_fares_compliant = filters.BooleanFilter()

    class Meta:
        form = FaresSearchFilterForm

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form

    def admin_areas_filter(self, queryset, name, value):
        # admin_area_names have been annotated onto the dataset

        if value:
            value = value.name
            queryset = queryset.filter(
                live_revision__metadata__faresmetadata__stops__admin_area__name=value
            ).distinct()
        return queryset
