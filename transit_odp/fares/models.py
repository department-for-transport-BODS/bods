from django.contrib.postgres.fields import ArrayField
from django.db import models

from transit_odp.fares.querysets import FaresNetexFileAttributesQuerySet
from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.models import DatasetMetadata


class DataCatalogueMetaData(models.Model):
    fares_metadata = models.ForeignKey(
        "fares.FaresMetadata",
        on_delete=models.CASCADE,
        related_name="datacatalogue",
    )
    xml_file_name = models.CharField(blank=True, max_length=255)
    valid_from = models.DateField(null=True, max_length=100)
    valid_to = models.DateField(null=True, max_length=100)
    national_operator_code = ArrayField(
        models.CharField(blank=True, max_length=255), null=True
    )
    line_id = ArrayField(models.CharField(blank=True, max_length=100), null=True)
    line_name = ArrayField(models.CharField(blank=True, max_length=100), null=True)
    atco_area = ArrayField(models.IntegerField(), null=True)
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
    stops = models.ManyToManyField(StopPoint, related_name="faresmetadata")

    objects = FaresNetexFileAttributesQuerySet.as_manager()
