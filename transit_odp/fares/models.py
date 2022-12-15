from django.contrib.postgres.fields import ArrayField
from django.db import models

from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.models import DatasetMetadata


class FaresDataCatalogueMetaData(models.Model):
    fares_metadata_id = models.ForeignKey(
        "fares.FaresMetadata",
        on_delete=models.CASCADE,
    )
    xml_file_name = models.CharField(blank=True, max_length=255)
    valid_from = models.DateField(null=True, max_length=100)
    valid_to = models.DateField(null=True, max_length=100)
    national_operator_code = ArrayField(
        models.CharField(blank=True, max_length=255), null=True
    )
    line_id = ArrayField(models.CharField(blank=True, max_length=255), null=True)
    line_name = ArrayField(models.CharField(blank=True, max_length=100), null=True)
    atco_area = ArrayField(models.CharField(blank=True, max_length=255), null=True)
    tariff_basis = ArrayField(models.CharField(blank=True, max_length=100), null=True)
    product_type = ArrayField(models.CharField(blank=True, max_length=100), null=True)
    product_name = ArrayField(models.CharField(blank=True, max_length=100), null=True)
    user_type = ArrayField(models.CharField(blank=True, max_length=100), null=True)


class FaresMetadata(DatasetMetadata):
    num_of_fare_zones = models.PositiveIntegerField()
    num_of_lines = models.PositiveIntegerField()
    num_of_sales_offer_packages = models.PositiveIntegerField()
    num_of_fare_products = models.PositiveIntegerField()
    num_of_user_profiles = models.PositiveIntegerField()
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    xml_file_name = ArrayField(models.CharField(null=True, max_length=255), null=True)
    fares_valid_from = ArrayField(
        models.CharField(null=True, max_length=100), null=True
    )
    fares_valid_to = ArrayField(models.CharField(null=True, max_length=100), null=True)
    national_operator_code = ArrayField(
        models.CharField(null=True, max_length=255), null=True
    )
    line_id = ArrayField(models.CharField(null=True, max_length=255), null=True)
    line_name = ArrayField(models.CharField(null=True, max_length=100), null=True)
    atco_area = ArrayField(models.CharField(null=True, max_length=255), null=True)
    tariff_basis = ArrayField(models.CharField(null=True, max_length=100), null=True)
    product_type = ArrayField(models.CharField(null=True, max_length=100), null=True)
    product_name = ArrayField(models.CharField(null=True, max_length=100), null=True)
    user_type = ArrayField(models.CharField(null=True, max_length=100), null=True)
    stops = models.ManyToManyField(StopPoint, related_name="faresmetadata")
    fares_data_catalogue_metadata = models.ManyToManyField(
        FaresDataCatalogueMetaData, related_name="faresmetadata"
    )
