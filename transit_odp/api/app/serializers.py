from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.models import DatasetRevision
from transit_odp.transmodel.models import ServicePattern


class DatasetRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetRevision
        fields = ["id", "dataset", "name"]


class DataQualityTaskStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    warning_count = serializers.IntegerField()


class StopPointSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = StopPoint
        geo_field = "location"
        fields = ["id", "atco_code", "location", "common_name"]


class ServicePatternSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ServicePattern
        geo_field = "geom"
        fields = [
            "id",
            "service_pattern_id",
            "revision",
            "origin",
            "destination",
            "description",
            "service_name",
        ]

    service_name = serializers.CharField(read_only=True)  # annotation
