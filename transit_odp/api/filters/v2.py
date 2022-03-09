from django_filters import rest_framework as filters

from transit_odp.common.filters import ArrayFilter
from transit_odp.organisation.models import Dataset, TXCFileAttributes


class OperatorFilterSet(filters.FilterSet):
    noc = filters.CharFilter(field_name="nocs__noc")
    licence = filters.CharFilter(field_name="licences__number")


class TimetableFilterSet(filters.FilterSet):
    noc = filters.CharFilter(
        field_name="live_revision__txc_file_attributes__national_operator_code"
    )
    line_name = ArrayFilter(
        field_name="live_revision__txc_file_attributes__line_names",
        lookup_expr="contains",
    )
    ordering = filters.OrderingFilter(
        fields=(
            ("live_revision__name", "name"),
            ("id", "id"),
            ("modified", "modified"),
        )
    )

    class Meta:
        model = Dataset
        fields = ["noc", "line_name"]


class TimetableFileFilterSet(filters.FilterSet):
    class Meta:
        model = TXCFileAttributes
        fields = ["noc", "line_name"]

    noc = filters.CharFilter(field_name="national_operator_code")
    line_name = ArrayFilter(field_name="line_names", lookup_expr="contains")
