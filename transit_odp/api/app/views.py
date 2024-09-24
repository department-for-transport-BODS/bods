from _elementtree import ParseError
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets, status as ResponseStatus
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_gis import filters as gis_filters
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes


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
from transit_odp.dqs.constants import ReportStatus, Level
from transit_odp.dqs.models import Report, ObservationResults
from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.models import DatasetRevision
from transit_odp.transmodel.models import ServicePattern


class DatasetRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DatasetRevision.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(methods=["get"], detail=True, url_path="dqs-status", url_name="dqs-status")
    def dqs_status(self, request, pk=None):
        """Extra action to return status of DQS report"""
        revision: DatasetRevision = self.get_object()
        return Response(revision.data_quality_tasks.get_latest_status())


class DQSDatasetRevisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Report.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    lookup_field = "revision_id"

    @action(methods=["get"], detail=True, url_path="dqs-status", url_name="dqs-status")
    def dqs_status(self, request, revision_id=None):
        """Extra action to return status of DQS report"""
        revision: Report = self.get_object()
        status = "PENDING"
        if revision.status in [
            ReportStatus.REPORT_GENERATED.value,
            ReportStatus.REPORT_GENERATION_FAILED.value,
        ]:
            status = "SUCCESS"
        return Response(status)


class DQSSuppressObservationViewSet(viewsets.ModelViewSet):
    queryset = ObservationResults.objects.all()
    # permission_classes = (IsAuthenticatedOrReadOnly,)
    # permission_classes = (IsAuthenticated, IsAuthenticatedOrReadOnly)

    @authentication_classes([])
    @action(
        methods=["get", "post"],
        detail=False,
        url_path="suppress_observation",
        url_name="suppress_observation",
    )
    def suppress_observation(self, request):
        """Action to suppress the observation result"""

        print(request.body)
        request_data = request.data
        print(f"request_data: {request_data}")
        # return Response(
        #     {"status": f"Updating rows"},
        #     status=ResponseStatus.HTTP_200_OK,
        #     headers={
        #         "Access-Control-Allow-Origin": "*",  # or specify your allowed origin
        #         "Access-Control-Allow-Credentials": "true",
        #     },
        # )

        report_id = request_data.get("report_id", None)
        revision_id = request_data.get("revision_id", None)
        org_id = request_data.get("organisation_id", None)
        service_code = request_data.get("service_code", None)
        line_name = request_data.get("line_name", None)
        check = request_data.get("check", None)
        is_suppressed = request_data.get("is_suppressed", False)

        if not (report_id and revision_id and org_id and check):
            return Response(
                {"error": "Required parameters are not sent"},
                status=ResponseStatus.HTTP_400_BAD_REQUEST,
            )

        observations = ObservationResults.objects.filter(
            taskresults__dataquality_report_id=report_id,
            taskresults__dataquality_report__revision_id=revision_id,
            taskresults__checks__observation=check,
            taskresults__checks__importance=Level.advisory.value,
        )
        if service_code and line_name:
            observations = observations.filter(
                taskresults__transmodel_txcfileattributes__service_code=service_code,
                taskresults__transmodel_txcfileattributes__service_txcfileattributes__name=line_name,
            )

        observation_count = len(observations)

        with transaction.atomic():
            observations.update(is_suppressed=is_suppressed)

        return Response(
            {"status": f"Updated successfully {observation_count} rows"},
            status=ResponseStatus.HTTP_200_OK,
        )


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
        url = f"{settings.DISRUPTIONS_API_BASE_URL}/organisations/{request.GET.get('orgId', None)}/disruptions"
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        content = []
        content, _ = _get_disruptions_organisation_data(url, headers)

        return JsonResponse(content, safe=False)


class DisruptionDetailView(viewsets.ViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def list(self, request):
        url = f"{settings.DISRUPTIONS_API_BASE_URL}/organisations/{request.GET.get('orgId', None)}/disruptions/{request.GET.get('disruptionId', None)}"
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        content = []
        content, _ = _get_disruptions_organisation_data(url, headers)

        consequence_coordinates = _get_coordinates_from_disruption(
            content["consequences"]
        )

        if len(consequence_coordinates) == 0:
            return JsonResponse(None, safe=False)

        map_data = _format_data_for_map(
            consequence_coordinates, content["disruptionReason"]
        )

        return JsonResponse(map_data, safe=False)


def _get_coordinates_from_disruption(disruption_consequences: list):
    consequence_coordinates = []
    for consequence in disruption_consequences:
        if consequence["consequenceType"] == "services":
            for service in consequence["services"]:
                if (
                    service["coordinates"]["latitude"]
                    and service["coordinates"]["longitude"] is not None
                ):
                    consequence_coordinates.append(service["coordinates"])

        if consequence["consequenceType"] == "stops":
            for stop in consequence["stops"]:
                if stop["latitude"] and stop["longitude"] is not None:
                    consequence_coordinates.append(
                        {
                            "latitude": stop["latitude"],
                            "longitude": stop["longitude"],
                        }
                    )

    return consequence_coordinates


def _format_data_for_map(consequence_coordinates: list, disruption_reason: str):
    map_data = []

    for coordinate in consequence_coordinates:
        map_data.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        coordinate["longitude"],
                        coordinate["latitude"],
                    ],
                },
                "properties": {"disruptionReason": disruption_reason},
            }
        )

    return map_data
