from django_hosts import reverse
from rest_framework import serializers

from config.hosts import DATA_HOST
from transit_odp.organisation.constants import STATUS_CHOICES
from transit_odp.organisation.models import (
    Dataset,
    Licence,
    OperatorCode,
    Organisation,
    TXCFileAttributes,
)


class NOCListField(serializers.RelatedField):
    def to_representation(self, operator_code: OperatorCode):
        return operator_code.noc


class LicenceListField(serializers.RelatedField):
    def to_representation(self, licence: Licence):
        return licence.number


class OperatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ["id", "name", "short_name", "nocs", "licences"]

    nocs = NOCListField(read_only=True, many=True)
    licences = LicenceListField(read_only=True, many=True)


class OperatorNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ["id", "name", "short_name"]


class TXCFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TXCFileAttributes
        exclude = ["revision"]

    dataset_id = serializers.IntegerField(source="revision.dataset_id")


class TimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        exclude = [
            "live_revision",
            "dataset_type",
            "contact",
            "avl_feed_status",
            "avl_feed_last_checked",
            "is_dummy",
            "subscribers",
            "organisation",
        ]

    name = serializers.CharField(source="live_revision.name")
    description = serializers.CharField(source="live_revision.description")
    status = serializers.ChoiceField(
        source="live_revision.status", choices=STATUS_CHOICES
    )
    download_url = serializers.SerializerMethodField(method_name="get_download_url")
    publisher_url = serializers.URLField(source="live_revision.url_link")
    files = TXCFileSerializer(many=True, source="live_revision.txc_file_attributes")
    operator = OperatorNameSerializer(source="organisation")

    def get_download_url(self, dataset):
        return reverse("feed-download", kwargs={"pk": dataset.id}, host=DATA_HOST)


class DatafeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        exclude = [
            "live_revision",
            "dataset_type",
            "contact",
            "avl_feed_last_checked",
            "is_dummy",
            "subscribers",
            "organisation",
        ]

    name = serializers.CharField(source="live_revision.name")
    description = serializers.CharField(source="live_revision.description")
    status = serializers.ChoiceField(
        source="live_revision.status", choices=STATUS_CHOICES
    )
    operator = OperatorNameSerializer(source="organisation")
