from rest_framework import generics, serializers
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny

from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import AVLType, FaresType, TimetableType
from transit_odp.organisation.models import Dataset, Organisation


class BrowseDatasetSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="live_revision.name")
    description = serializers.CharField(source="live_revision.description")
    status = serializers.CharField(source="live_revision.status")
    modified = serializers.DateTimeField(source="live_revision.modified")
    operatorName = serializers.CharField(source="organisation.name")
    firstStartDate = serializers.DateTimeField(
        source="live_revision.first_service_start", allow_null=True
    )
    avl_feed_last_checked = serializers.DateTimeField(allow_null=True)
    adminAreas = serializers.SerializerMethodField()

    class Meta:
        model = Dataset
        fields = (
            "id",
            "name",
            "description",
            "status",
            "modified",
            "operatorName",
            "firstStartDate",
            "avl_feed_last_checked",
            "adminAreas",
        )

    def get_adminAreas(self, dataset):
        return [
            {"id": area.id, "name": area.name}
            for area in dataset.live_revision.admin_areas.all()
        ]


class BrowsePagination(LimitOffsetPagination):
    default_limit = 500
    max_limit = 500


class BrowseDatasetListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = BrowseDatasetSerializer
    pagination_class = BrowsePagination
    dataset_type = None

    def get_queryset(self):
        queryset = (
            Dataset.objects.get_published()
            .get_active_org()
            .filter(dataset_type=self.dataset_type)
            .select_related("live_revision", "organisation")
            .prefetch_related("live_revision__admin_areas")
            .order_by("-live_revision__published_at")
        )
        return queryset


class BrowseTimetableListView(BrowseDatasetListView):
    dataset_type = TimetableType

    def get_queryset(self):
        return super().get_queryset().get_viewable_statuses()


class BrowseAVLListView(BrowseDatasetListView):
    dataset_type = AVLType


class BrowseFaresListView(BrowseDatasetListView):
    dataset_type = FaresType

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .get_viewable_statuses()
            .get_compliant_fares_validation()
        )


class BrowseAdminAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminArea
        fields = ("id", "name")


class BrowseAdminAreaListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = BrowseAdminAreaSerializer
    queryset = AdminArea.objects.all().order_by("name")
    pagination_class = BrowsePagination


class BrowseOrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ("id", "name")


class BrowseOrganisationListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = BrowseOrganisationSerializer
    queryset = Organisation.objects.filter(is_active=True).order_by("name")
    pagination_class = BrowsePagination
