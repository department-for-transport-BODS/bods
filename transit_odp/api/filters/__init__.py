from django.db.models import Q
from django_filters import rest_framework as filters

from transit_odp.common.utils.date_validator import validate
from transit_odp.data_quality.scoring import AMBER_THRESHOLD, GREEN_THRESHOLD
from transit_odp.organisation.models import Dataset, Organisation

STATUS_CHOICE = (
    ("inactive", "Inactive"),
    ("published", "Published"),
    ("error", "Error"),
)


class DatasetSearchFilterSet(filters.FilterSet):
    noc = filters.CharFilter(method="noc_filter")
    modifiedDate = filters.CharFilter(method="last_modified_filter")
    adminArea = filters.CharFilter(method="admin_areas_filter")
    startDateStart = filters.CharFilter(method="feed_start_date_start_filter")
    startDateEnd = filters.CharFilter(method="feed_start_date_end_filter")
    endDateStart = filters.CharFilter(method="feed_end_date_start_filter")
    endDateEnd = filters.CharFilter(method="feed_end_date_end_filter")
    dqRag = filters.ChoiceFilter(
        method="rag_filter",
        choices=(("red", "red"), ("amber", "amber"), ("green", "green")),
    )
    bodsCompliance = filters.BooleanFilter(field_name="is_pti_compliant")

    def noc_filter(self, queryset, name, value):
        if value:
            noc_list = list(value.split(","))
            organisations = (
                Organisation.objects.filter(nocs__noc__in=noc_list)
                .order_by("id")
                .distinct("id")
            )

            queryset = queryset.filter(organisation__in=organisations)
        return queryset

    def last_modified_filter(self, queryset, name, value):
        if value:
            if validate(value):
                queryset = queryset.filter(Q(modified__gte=value))
        return queryset

    def admin_areas_filter(self, queryset, name, value):
        if value:
            admin_area_list = list(value.split(","))
            queryset = queryset.filter(
                Q(live_revision__admin_areas__atco_code__in=admin_area_list)
            )
        return queryset

    def feed_start_date_start_filter(self, queryset, name, value):
        if value:
            if validate(value):
                queryset = queryset.filter(
                    Q(live_revision__first_service_start__gte=value)
                    | Q(live_revision__first_service_start__isnull=True)
                )
        return queryset

    def feed_start_date_end_filter(self, queryset, name, value):
        if value:
            if validate(value):
                queryset = queryset.filter(
                    Q(live_revision__first_service_start__lte=value)
                    | Q(live_revision__first_service_start__isnull=True)
                )
        return queryset

    def feed_end_date_start_filter(self, queryset, name, value):
        if value:
            if validate(value):
                queryset = queryset.filter(
                    Q(live_revision__last_expiring_service__gte=value)
                    | Q(live_revision__last_expiring_service__isnull=True)
                )
        return queryset

    def feed_end_date_end_filter(self, queryset, name, value):
        if value:
            if validate(value):
                queryset = queryset.filter(
                    Q(live_revision__last_expiring_service__lte=value)
                    | Q(live_revision__last_expiring_service__isnull=True)
                )
        return queryset

    def rag_filter(self, queryset, name, value):
        query_map = {
            "green": Q(score__gte=GREEN_THRESHOLD),
            "amber": Q(score__lt=GREEN_THRESHOLD, score__gt=AMBER_THRESHOLD),
            "red": Q(score__gt=0, score__lte=AMBER_THRESHOLD),
        }
        if value:
            queryset = queryset.filter(query_map[value])

        return queryset


class NOCFilter(filters.BaseInFilter, filters.CharFilter):
    pass


def filter_status(queryset, name, value):
    """Hack since in the backend status can be "live" but in the public API
    this needs to be "published".
    """
    if value == "published":
        return queryset.filter(**{name: "live"})
    return queryset.filter(**{name: value})


class FaresDatasetFilterSet(filters.FilterSet):
    status = filters.ChoiceFilter(
        field_name="live_revision__status", choices=STATUS_CHOICE, method=filter_status
    )
    noc = NOCFilter(field_name="organisation__nocs__noc", lookup_expr="in")

    class Meta:
        model = Dataset
        fields = ["status", "noc"]
