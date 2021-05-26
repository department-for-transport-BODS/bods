from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Polygon
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from transit_odp.api import filters
from transit_odp.api.serializers import FaresDatasetSerializer
from transit_odp.api.validators import (
    validate_api_parameter_keys,
    validate_api_parameter_values,
)
from transit_odp.api.views import DatasetBaseViewSet
from transit_odp.common.utils.get_bounding_box import get_bounding_box
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset

FARES = DatasetType.FARES.value

valid_parameters = [
    "limit",
    "offset",
    "noc",
    "boundingBox",
    "api_key",
    "status",
    "format",
]


class FaresDatasetViewset(DatasetBaseViewSet):
    dataset_type = FARES
    permission_classes = (IsAuthenticated,)
    serializer_class = FaresDatasetSerializer
    filterset_class = filters.FaresDatasetFilterSet

    def list(self, request, *args, **kwargs):
        # Check for invalid query parameter keys and values
        invalid_parameter_keys = validate_api_parameter_keys(
            self.request.query_params, valid_parameters
        )
        invalid_parameter_values = validate_api_parameter_values(
            self.request.query_params
        )
        # TODO could be refactored to handle invalid keys and
        # values in the same Response
        if len(invalid_parameter_keys) > 0:
            content = {"Unsupported query parameter": invalid_parameter_keys}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        if len(invalid_parameter_values) > 0:
            content = {
                "Unsupported query parameter value for": invalid_parameter_values
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        return super().list(self, request, *args, **kwargs)

    def get_queryset(self):
        qs = (
            Dataset.objects.get_published()
            .filter(dataset_type=DatasetType.FARES.value)
            .get_active_org()
            .add_organisation_name()
            .select_related("live_revision")
            .prefetch_related("organisation__nocs")
            .prefetch_related("live_revision__metadata__faresmetadata__stops")
        )

        status_list = self.request.GET.getlist("status", [])

        if status_list and "" not in status_list:
            status_list = [
                status.replace("published", "live") for status in status_list
            ]
            qs = qs.filter(live_revision__status__in=status_list)

        bounding_box = self.request.GET.getlist("boundingBox", [])
        if bounding_box:
            box = get_bounding_box(bounding_box)
            geom = Polygon.from_bbox(box)
            qs = qs.filter(
                live_revision__metadata__faresmetadata__stops__location__within=geom
            )
        qs = qs.order_by("id").distinct()

        return qs


class FaresOpenApiView(LoginRequiredMixin, TemplateView):
    """View for Fares Dataset API."""

    template_name = "swagger_ui/fares.html"
