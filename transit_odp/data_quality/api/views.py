from django.db.models import (
    BooleanField,
    Case,
    CharField,
    OuterRef,
    Subquery,
    Value,
    When,
)
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from transit_odp.api.pagination import GeoJsonPagination
from transit_odp.data_quality.api.filters import (
    ServiceLinkFilterSet,
    ServicePatternFilterSet,
    StopPointFilterSet,
)
from transit_odp.data_quality.api.serializers import (
    ServiceLinkSerializer,
    ServicePatternSerializer,
    StopPointSerializer,
)
from transit_odp.data_quality.models import ServiceLink, ServicePattern, StopPoint


class StopPointViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Data Quality Stop Points
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = StopPointSerializer
    pagination_class = GeoJsonPagination
    filterset_class = StopPointFilterSet
    queryset = StopPoint.objects.all().order_by("id")

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        effected_stop_ids = self.request.query_params.get("effected")
        if effected_stop_ids:
            effected_stop_ids = effected_stop_ids.split(",")
            qs = qs.annotate(
                effected=Case(
                    When(
                        id__in=effected_stop_ids,
                        then=Value(True, output_field=BooleanField()),
                    ),
                    default=Value(False, output_field=BooleanField()),
                )
            )
        return qs


class ServicePatternViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Data Quality Service Patterns
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ServicePatternSerializer
    pagination_class = GeoJsonPagination
    filterset_class = ServicePatternFilterSet
    queryset = ServicePattern.objects.all().order_by("id")


class ServiceLinkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Data Quality Service Links
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = ServiceLinkSerializer
    pagination_class = GeoJsonPagination
    filterset_class = ServiceLinkFilterSet
    queryset = ServiceLink.objects.all().order_by("id")

    # Annotate after initial filtering to avoid annotating all instances
    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        # TODO: stop getting arbitrary service pattern
        # models mean we currently have to get arbitrary service pattern for
        # service links to use in template and map
        service_name_subquery = (
            ServicePattern.objects.filter(id=OuterRef("service_patterns"))
            .order_by("ito_id")
            .values_list("service__name")[:1]
        )
        qs = qs.annotate(
            service_name=Subquery(service_name_subquery, output_field=CharField()),
        ).distinct("id")
        return qs
