from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from transit_odp.data_quality.models import ServiceLink, ServicePattern, StopPoint


class StopPointSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = StopPoint
        geo_field = "geometry"
        fields = ["id", "effected", "name", "atco_code"]

    # If no effected stops passed to API, StopPoints won't be annotated with
    # effected=True/False, so need default
    effected = serializers.BooleanField(read_only=True, default=False)


class ServicePatternSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ServicePattern
        geo_field = "geometry"
        # can use auto_bbox=True and use that output instead of calculating
        # bounding box in JS?
        fields = ["id", "service_name"]

    # define as service_name for consistency in frontend
    service_name = serializers.CharField(source="name", read_only=True)


class ServiceLinkSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ServiceLink
        geo_field = "geometry"
        fields = ["id", "service_name"]

    # added by annotation so throws error unless specified here
    service_name = serializers.CharField(read_only=True)
