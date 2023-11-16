from rest_framework import serializers

from transit_odp.data_quality.scoring import DataQualityRAG
from transit_odp.naptan.models import AdminArea, Locality
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset

FARES_EXCLUDED_FIELDS = (
    "avl_feed_last_checked",
    "avl_feed_status",
    "contact",
    "subscribers",
    "live_revision",
    "organisation",
    "dataset_type",
    "is_dummy",
)
GMT_FORMAT = "%Y-%m-%dT%H:%M:%S+00:00"


class StatusField(serializers.Field):
    def to_representation(self, value):
        if value == "live":
            return "published"
        return value

    def to_internal_value(self, value):
        if value == "published":
            return "live"
        return value


class NOCStringField(serializers.RelatedField):
    def to_representation(self, value):
        return value.noc


class DatasetTypeField(serializers.Field):
    def to_representation(self, value):
        return DatasetType(value).name


class AdminAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminArea
        fields = ["atco_code", "name"]


class LocalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Locality
        fields = ["gazetteer_id", "name"]


class FaresDatasetSerializer(serializers.ModelSerializer):
    created = serializers.DateTimeField(
        source="live_revision.created", format=GMT_FORMAT
    )
    modified = serializers.DateTimeField(
        source="live_revision.modified", format=GMT_FORMAT
    )
    operatorName = serializers.CharField(source="organisation.name")
    noc = NOCStringField(source="organisation.nocs", many=True, read_only=True)
    name = serializers.CharField(source="live_revision.name")
    description = serializers.CharField(source="live_revision.description")
    comment = serializers.CharField(source="live_revision.comment")
    status = StatusField(source="live_revision.status")
    url = serializers.URLField(source="download_url")
    startDate = serializers.DateTimeField(
        source="live_revision.metadata.faresmetadata.valid_from", format=GMT_FORMAT
    )
    endDate = serializers.DateTimeField(
        source="live_revision.metadata.faresmetadata.valid_to", format=GMT_FORMAT
    )
    numOfLines = serializers.IntegerField(
        source="live_revision.metadata.faresmetadata.num_of_lines"
    )
    numOfFareZones = serializers.IntegerField(
        source="live_revision.metadata.faresmetadata.num_of_fare_zones"
    )
    numOfSalesOfferPackages = serializers.IntegerField(
        source="live_revision.metadata.faresmetadata.num_of_sales_offer_packages"
    )
    numOfFareProducts = serializers.IntegerField(
        source="live_revision.metadata.faresmetadata.num_of_fare_products"
    )
    numOfUserTypes = serializers.IntegerField(
        source="live_revision.metadata.faresmetadata.num_of_user_profiles"
    )
    extension = serializers.CharField(source="live_revision.upload_file_extension")

    class Meta:
        model = Dataset
        exclude = FARES_EXCLUDED_FIELDS


class DatasetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    created = serializers.DateTimeField(format=GMT_FORMAT)
    modified = serializers.DateTimeField(
        format=GMT_FORMAT, source="live_revision.published_at"
    )
    operatorName = serializers.CharField(source="organisation.name")
    noc = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="noc", source="organisation.nocs"
    )

    name = serializers.CharField(source="live_revision.name")
    description = serializers.CharField(source="live_revision.description")
    comment = serializers.CharField(source="live_revision.comment")
    status = serializers.SerializerMethodField("get_feed_status")
    url = serializers.URLField(source="download_url")
    extension = serializers.CharField(source="live_revision.upload_file_extension")

    lines = serializers.SerializerMethodField("get_lines")
    firstStartDate = serializers.DateTimeField(
        source="live_revision.first_service_start", format=GMT_FORMAT
    )
    firstEndDate = serializers.DateTimeField(
        source="live_revision.first_expiring_service", format=GMT_FORMAT
    )
    lastEndDate = serializers.DateTimeField(
        source="live_revision.last_expiring_service", format=GMT_FORMAT
    )
    adminAreas = AdminAreaSerializer(many=True, source="live_revision.admin_areas")
    localities = LocalitySerializer(many=True, source="live_revision.localities")

    dqScore = serializers.SerializerMethodField("get_score")
    dqRag = serializers.SerializerMethodField("get_RAG")
    bodsCompliance = serializers.SerializerMethodField("get_bods_compliance")

    def get_score(self, feed):
        value = feed.score if feed.score else 0
        # To overcome an issue where 0.999
        # is rounded to 1 which inturn returns
        # 100% instead of 99.9%
        if 0.99 < value < 1:
            value = int(value * 1000) / 1000.0
        return f"{value*100:.1f}%"

    def get_RAG(self, feed):
        value = feed.score
        if value:
            return DataQualityRAG.from_score(value).rag_level
        return "unavailable"

    def get_bods_compliance(self, feed):
        if not feed.is_after_pti_compliance_date:
            return None
        return feed.is_pti_compliant

    def get_lines(self, feed):
        line_names_set = set()
        # Do not add more filters as it will cause (n+1) issue. If we need to add more
        # filtering to this in future, its worth moving this to an annotation
        # Reference - https://docs.djangoproject.com/en/2.2/ref/models/querysets/
        # #prefetch-related
        # TODO move this to Dataset queryset method
        services = feed.live_revision.services.all()

        for service in services:
            line_names_set.add(service.name)
            for other_name in service.other_names:
                line_names_set.add(other_name)

        return sorted(line_names_set)

    def get_feed_status(self, feed):
        return (
            feed.live_revision.status
            if feed.live_revision.status != "live"
            else "published"
        )
