from _elementtree import ParseError
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from config import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_gis import filters as gis_filters

from transit_odp.api.app.filters import ServicePatternFilterSet
from transit_odp.api.app.serializers import (
    ServicePatternSerializer,
    StopPointSerializer,
)
from transit_odp.api.pagination import GeoJsonPagination
from transit_odp.browse.views.disruptions_views import (
    _get_disruptions_organisation_data,
)
from transit_odp.fares.models import FaresMetadata
from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.models import DatasetRevision
from transit_odp.transmodel.models import ServicePattern

from django.views import View
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView


class DatasetRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DatasetRevision.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(methods=["get"], detail=True, url_path="dqs-status", url_name="dqs-status")
    def dqs_status(self, request, pk=None):
        """Extra action to return status of DQS report"""
        revision: DatasetRevision = self.get_object()
        return Response(revision.data_quality_tasks.get_latest_status())


class StopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View Naptan StopPoints
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = StopPointSerializer
    pagination_class = GeoJsonPagination
    # pagination_class = None
    search_fields = ["common_name", "street", "atco_code", "naptan_code"]
    ordering_fields = ["atco_code", "naptan_code", "common_name"]
    ordering = ("atco_code",)
    bbox_filter_field = "location"
    distance_filter_field = "location"
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
        gis_filters.InBBoxFilter,
        gis_filters.DistanceToPointFilter,
    )
    bbox_filter_include_overlapping = True
    distance_filter_convert_meters = True

    def get_queryset(self):
        qs = StopPoint.objects.all().order_by("atco_code")

        point_string = self.request.query_params.get("point", None)
        if point_string:
            try:
                (x, y) = (float(n) for n in point_string.split(","))
            except ValueError:
                raise ParseError("Invalid geometry string supplied for parameter point")

            p = Point(x, y, srid=4326)

            qs = qs.annotate(distance=Distance("location", p)).order_by("distance")

        return qs


class ServicePatternViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View service patterns indexed within uploaded transXchange datasets
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ServicePatternSerializer
    pagination_class = GeoJsonPagination
    filterset_class = ServicePatternFilterSet

    def get_queryset(self):
        return ServicePattern.objects.all().add_service_name()


class FareStopsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View stop points indexed within a Fares data set
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = StopPointSerializer
    pagination_class = GeoJsonPagination

    def get_queryset(self):
        revision_id = self.request.GET.get("revision", "")
        return FaresMetadata.objects.get(revision_id=revision_id).stops.all()


class DisruptionsInOrganisationView(viewsets.ViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def list(self, request):
        url = f"{settings.DISRUPTIONS_API_BASE_URL}/organisations/{request.GET.get('pk', None)}/impacted/stops"
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        content = []
        content, _ = _get_disruptions_organisation_data(url, headers)

        servicesGeoJson = {
            "type": "FeatureCollection",
            "count": len(content),
            "features": content["services"],
        }

        stopsGeoJson = {
            "type": "FeatureCollection",
            "count": len(content),
            "features": content["stops"],
        }

        geoJson = {"stops": stopsGeoJson, "services": servicesGeoJson}

        return JsonResponse(geoJson)
