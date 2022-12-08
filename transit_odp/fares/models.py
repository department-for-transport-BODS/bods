from django.db import models

from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.models import DatasetMetadata
from transit_odp.fares.querysets import FaresNetexFileAttributesQuerySet


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

