from rest_framework import serializers

from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset


class DatasetCatalogueSerializer(serializers.ModelSerializer):
    operator = serializers.CharField(source="organisation_name")
    dataType = serializers.SerializerMethodField("get_dataset_type")
    status = serializers.SerializerMethodField("get_feed_status")
    lastUpdated = serializers.DateTimeField(source="modified")
    dataID = serializers.IntegerField(source="id")

    class Meta:
        model = Dataset
        fields = ("operator", "dataType", "status", "lastUpdated", "dataID")

    def get_dataset_type(self, feed):
        if feed.dataset_type == DatasetType.TIMETABLE.value:
            return "Timetables"
        elif feed.dataset_type == DatasetType.AVL.value:
            return "Automatic Vehicle Locations (AVL)"
        else:
            return "Fares"

    def get_feed_status(self, feed):
        if (
            feed.dataset_type == DatasetType.AVL.value
            and feed.live_revision.status == FeedStatus.error.value
        ):
            return "Data unavailable"
        return (
            feed.live_revision.status
            if feed.live_revision.status != "live"
            else "published"
        )
