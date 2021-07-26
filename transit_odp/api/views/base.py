from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from transit_odp.api.filters import DatasetSearchFilterSet
from transit_odp.api.serializers import DatasetSerializer
from transit_odp.api.validators import (
    validate_api_parameter_keys,
    validate_api_parameter_values,
)
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset

valid_parameters = [
    "limit",
    "offset",
    "noc",
    "modifiedDate",
    "adminArea",
    "startDateStart",
    "startDateEnd",
    "endDateStart",
    "endDateEnd",
    "status",
    "search",
    "api_key",
    "format",
    "dqRag",
    "bodsCompliance",
]


class DatasetBaseViewSet(viewsets.ReadOnlyModelViewSet):
    dataset_type = DatasetType.TIMETABLE.value
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = (
            Dataset.objects.filter(dataset_type=self.dataset_type)
            .get_published()
            .get_active_org()
            .add_organisation_name()
            .select_related("live_revision")
        )
        return queryset


class DatasetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View feeds
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = DatasetSerializer
    filterset_class = DatasetSearchFilterSet
    search_fields = [
        "live_revision__name",
        "live_revision__description",
        "organisation__name",
        "live_revision__admin_areas__name",
    ]

    def list(self, request, *args, **kwargs):
        # Check for invalid query parameter keys and values
        invalid_parameter_keys = validate_api_parameter_keys(
            self.request.query_params, valid_parameters
        )
        invalid_parameter_values = validate_api_parameter_values(
            self.request.query_params
        )
        # TODO could be refactored to handle invalid keys and values in the
        # same Response
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
        # Filter results to only those that are live, error or expired and Published
        qs = (
            Dataset.objects.get_published()
            .get_active_org()
            .add_organisation_name()
            .select_related("live_revision")
            .prefetch_related("organisation__nocs")
            .prefetch_related("live_revision__admin_areas")
            .prefetch_related("live_revision__localities")
            .prefetch_related("live_revision__services")
        )

        # Handle a list of feed status
        status_list = self.request.GET.getlist("status", [])

        if status_list and "" not in status_list:
            status_list = [
                status.replace("published", "live") for status in status_list
            ]
            qs = qs.filter(live_revision__status__in=status_list)

        # Get search terms
        keywords = self.request.GET.get("search", "").strip()

        if keywords:
            # TODO - enable full-text search
            # query = SearchQuery(keywords)
            # vector = SearchVector('name', 'description')
            # qs = qs.annotate(search=vector).filter(search=query)
            # qs = qs.annotate(rank=SearchRank(vector, query)).order_by('-rank')
            qs = qs.filter(
                Q(live_revision__name__icontains=keywords)
                | Q(live_revision__description__icontains=keywords)
                | Q(organisation_name__icontains=keywords)
                | Q(live_revision__admin_areas__name__icontains=keywords)
            )

        # Make the search results distinct since there will be duplicates from the
        # join with admin_areas
        qs = qs.order_by("id").distinct()

        return qs
