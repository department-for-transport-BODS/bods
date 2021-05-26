from django_filters import rest_framework as filters

from transit_odp.transmodel.models import ServicePattern


class ServicePatternFilterSet(filters.FilterSet):
    class Meta:
        model = ServicePattern
        fields = ["revision"]
