from django_filters import rest_framework as filters

from transit_odp.transmodel.models import ServicePattern


class ServicePatternFilterSet(filters.FilterSet):
    service_codes = filters.CharFilter(
        field_name="services__service_code", method="filter_by_service_codes"
    )

    class Meta:
        model = ServicePattern
        fields = ["revision", "line_name", "service_codes"]

    def filter_by_service_codes(self, queryset, name, value):
        service_codes_list = value.split(",")
        return queryset.filter(services__service_code__in=service_codes_list)
