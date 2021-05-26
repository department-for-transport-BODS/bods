from django_filters import rest_framework as filters

from transit_odp.data_quality.models import ServiceLink, ServicePattern, StopPoint


class StopPointFilterSet(filters.FilterSet):
    class Meta:
        model = StopPoint
        fields = {"id": ["exact", "in"]}


class ServicePatternFilterSet(filters.FilterSet):
    class Meta:
        model = ServicePattern
        fields = ["id"]


class ServiceLinkFilterSet(filters.FilterSet):
    class Meta:
        model = ServiceLink
        fields = {"id": ["exact", "in"]}
