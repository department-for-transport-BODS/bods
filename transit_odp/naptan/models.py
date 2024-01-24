from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from transit_odp.common.utils.repr import nice_repr
from transit_odp.naptan.managers import (
    AdminAreaManager,
    LocalityManager,
    StopPointManager,
    FlexibleZoneManager,
)
from django.db.models import UniqueConstraint


class AdminArea(models.Model):
    class Meta:
        ordering = ("name",)

    def __repr__(self):
        return nice_repr(self)

    name = models.CharField(max_length=255)
    traveline_region_id = models.CharField(max_length=255)
    atco_code = models.CharField(max_length=255, unique=True)
    ui_lta = models.ForeignKey(
        "otc.UILta",
        related_name="naptan_ui_lta_records",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )

    objects = AdminAreaManager()


class District(models.Model):
    class Meta:
        ordering = ("name",)

    name = models.CharField(max_length=255)

    def __repr__(self):
        return nice_repr(self)


class Locality(models.Model):
    class Meta:
        ordering = ("name",)

    gazetteer_id = models.CharField(max_length=8, primary_key=True)
    name = models.CharField(max_length=255)
    district = models.ForeignKey(
        District, on_delete=models.SET_NULL, null=True, blank=True
    )
    admin_area = models.ForeignKey(
        AdminArea, on_delete=models.SET_NULL, null=True, blank=True
    )
    easting = models.IntegerField()
    northing = models.IntegerField()

    def __repr__(self):
        return nice_repr(self)

    objects = LocalityManager()


class StopPoint(models.Model):
    class Meta:
        ordering = ("atco_code",)

    atco_code = models.CharField(max_length=255, unique=True)
    naptan_code = models.CharField(max_length=12, null=True, blank=True)
    common_name = models.CharField(max_length=255)
    street = models.CharField(max_length=255, null=True, blank=True)
    indicator = models.CharField(max_length=255, null=True, blank=True)
    location = models.PointField()
    locality = models.ForeignKey(
        Locality, related_name="stops", on_delete=models.SET_NULL, null=True, blank=True
    )
    admin_area = models.ForeignKey(
        AdminArea,
        related_name="stops",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    stop_areas = ArrayField(
        models.CharField(max_length=255),
        default=list,
    )
    stop_type = models.CharField(max_length=255, null=True, blank=True)
    bus_stop_type = models.CharField(max_length=255, null=True, blank=True)

    objects = StopPointManager()

    def __repr__(self):
        return nice_repr(self)


class FlexibleZone(models.Model):
    class Meta:
        ordering = ("naptan_stoppoint", "sequence_number")
        constraints = [
            UniqueConstraint(
                fields=["naptan_stoppoint", "sequence_number"],
                name="unique_flexible_zone",
            ),
        ]
    naptan_stoppoint = models.ForeignKey(
        StopPoint, related_name="flexible_zones", on_delete=models.CASCADE
    )
    sequence_number = models.IntegerField()
    location = models.PointField()

    objects = FlexibleZoneManager()

    def __repr__(self):
        return nice_repr(self)
