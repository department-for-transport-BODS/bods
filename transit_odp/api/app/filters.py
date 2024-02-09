from django_filters import rest_framework as filters

from transit_odp.transmodel.models import ServicePattern


class ServicePatternFilterSet(filters.FilterSet):
    service_name = filters.CharFilter(field_name="services__name", lookup_expr="exact")

    class Meta:
        model = ServicePattern
        fields = ["revision", "service_name"]
