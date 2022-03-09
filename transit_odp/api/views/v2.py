from rest_framework.viewsets import ReadOnlyModelViewSet

from transit_odp.api.filters.v2 import (
    OperatorFilterSet,
    TimetableFileFilterSet,
    TimetableFilterSet,
)
from transit_odp.api.serializers.v2 import (
    DatafeedSerializer,
    OperatorSerializer,
    TimetableSerializer,
    TXCFileSerializer,
)
from transit_odp.organisation.constants import AVLType, TimetableType
from transit_odp.organisation.models import Dataset, Organisation, TXCFileAttributes


class OperatorViewSet(ReadOnlyModelViewSet):
    serializer_class = OperatorSerializer
    ordering_fields = ["id", "name", "short_name"]
    filterset_class = OperatorFilterSet

    def get_queryset(self):
        return (
            Organisation.objects.filter(is_active=True)
            .prefetch_related("licences", "nocs")
            .order_by("id")
        )


class DatafeedViewSet(ReadOnlyModelViewSet):
    serializer_class = DatafeedSerializer
    ordering_fields = ["id", "modified"]

    def get_queryset(self):
        return (
            Dataset.objects.get_published()
            .get_active_org()
            .select_related("live_revision", "organisation")
            .filter(dataset_type=AVLType, is_dummy=False)
        )


class TimetableViewSet(ReadOnlyModelViewSet):
    serializer_class = TimetableSerializer
    filterset_class = TimetableFilterSet

    def get_queryset(self):
        return (
            Dataset.objects.get_published()
            .get_active_org()
            .select_related("live_revision", "organisation")
            .prefetch_related("live_revision__txc_file_attributes")
            .filter(dataset_type=TimetableType, is_dummy=False)
        )


class TimetableFilesViewSet(ReadOnlyModelViewSet):
    serializer_class = TXCFileSerializer
    filterset_class = TimetableFileFilterSet
    ordering_fields = ["id", "operating_period_start_date", "filename"]

    def get_queryset(self):
        return TXCFileAttributes.objects.get_active_live_revisions().select_related(
            "revision"
        )
