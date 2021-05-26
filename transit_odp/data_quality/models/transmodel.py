"""
transmodel.py

This defines a set of transmodel / naptan models independent from those used by BODS
to reduce the complexity of integrating DQS. Furthermore, we want the data within each
report to be independent of other reports. This ensures the report's warnings remain
consistent at the time they were generated and are not affected by the evolution of
NaPTaN data in BODS or DQS (which are governed by independent processes) nor are
clobbered by merging the same entities from different reports.
"""
from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import DateField

from transit_odp.data_quality.dataclasses.features import Line
from transit_odp.data_quality.models import DataQualityReport
from transit_odp.data_quality.models.querysets import (
    TimingPatternStopQueryset,
    VehicleJourneyQueryset,
)


class Service(models.Model):
    ito_id = models.TextField(unique=True)
    name = models.CharField(max_length=255)
    reports = models.ManyToManyField(DataQualityReport, related_name="services")

    @classmethod
    def from_line(cls, line: Line):
        return cls(ito_id=line.id, name=line.name)

    def __str__(self):
        return f"id={self.id}, ito_id={self.ito_id!r}, name={self.name!r}"


class ServicePattern(models.Model):
    ito_id = models.TextField(unique=True)
    service = models.ForeignKey(
        "data_quality.Service",
        on_delete=models.CASCADE,
        related_name="service_patterns",
    )
    name = models.CharField(max_length=255)
    geometry = models.LineStringField()
    stops = models.ManyToManyField(
        "data_quality.StopPoint",
        through="data_quality.ServicePatternStop",
        related_name="service_patterns",
    )
    service_links = models.ManyToManyField(
        "data_quality.ServiceLink",
        through="data_quality.ServicePatternServiceLink",
        related_name="service_patterns",
    )

    def __str__(self):
        return f"id={self.id}, ito_id={self.ito_id!r}, name={self.name!r}"


class ServicePatternStop(models.Model):
    service_pattern = models.ForeignKey(
        "data_quality.ServicePattern",
        on_delete=models.CASCADE,
        related_name="service_pattern_stops",
    )
    stop = models.ForeignKey(
        "data_quality.StopPoint",
        related_name="service_pattern_stops",
        on_delete=models.PROTECT,
    )
    position = models.IntegerField()

    def __str__(self):
        return (
            f"id={self.id}, "
            f"position={self.position}, "
            f"stop={self.stop.name!r}, "
            f"service_pattern={self.service_pattern.name!r}"
        )

    class Meta:
        unique_together = ("service_pattern", "stop", "position")


class ServicePatternServiceLink(models.Model):
    service_pattern = models.ForeignKey(
        "data_quality.ServicePattern",
        on_delete=models.CASCADE,
        related_name="service_pattern_service_links",
    )
    service_link = models.ForeignKey(
        "data_quality.ServiceLink",
        related_name="service_pattern_service_links",
        on_delete=models.PROTECT,
    )
    position = models.IntegerField()

    def __str__(self):
        return (
            f"id={self.id}, service_pattern={self.service_pattern.ito_id!r}, "
            f"service_link={self.service_link.ito_id!r}, position={self.position}"
        )

    class Meta:
        unique_together = ("service_pattern", "service_link", "position")


class TimingPattern(models.Model):
    ito_id = models.TextField(unique=True)
    service_pattern = models.ForeignKey(
        "data_quality.ServicePattern",
        on_delete=models.CASCADE,
        related_name="timing_patterns",
    )

    def __str__(self):
        return (
            f"id={self.id}, "
            f"ito_id={self.ito_id!r}, "
            f"service_pattern={self.service_pattern.name!r}"
        )


class TimingPatternStop(models.Model):
    timing_pattern = models.ForeignKey(
        "data_quality.TimingPattern",
        on_delete=models.CASCADE,
        related_name="timing_pattern_stops",
    )
    service_pattern_stop = models.ForeignKey(
        "data_quality.ServicePatternStop",
        on_delete=models.CASCADE,
        related_name="timings",
    )
    arrival = models.DurationField(
        help_text=(
            "The duration of time from the Vehicle Journey start time to "
            "reach service_pattern_stop"
        )
    )
    departure = models.DurationField(
        help_text=(
            "The duration of time from the Vehicle Journey start time to depart "
            "service_pattern_stop"
        )
    )
    pickup_allowed = models.BooleanField(default=True)
    setdown_allowed = models.BooleanField(default=True)
    timing_point = models.BooleanField(default=False)

    objects = TimingPatternStopQueryset.as_manager()

    def __str__(self):
        return (
            f"id={self.id}, "
            f"timing_pattern={self.timing_pattern.ito_id!r}, "
            f"stop={self.service_pattern_stop.stop.name!r}"
        )


class ServiceLink(models.Model):
    ito_id = models.TextField(unique=True)
    geometry = models.LineStringField(null=True)
    from_stop = models.ForeignKey(
        "data_quality.StopPoint",
        related_name="from_service_links",
        on_delete=models.PROTECT,
    )
    to_stop = models.ForeignKey(
        "data_quality.StopPoint",
        related_name="to_service_links",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return f"id={self.id}, ito_id={self.ito_id!r}"

    class Meta:
        unique_together = ("from_stop", "to_stop")


class VehicleJourney(models.Model):
    ito_id = models.TextField(unique=True)
    timing_pattern = models.ForeignKey(
        TimingPattern, on_delete=models.CASCADE, related_name="vehicle_journeys"
    )
    start_time = models.TimeField()
    dates = ArrayField(DateField())

    objects = VehicleJourneyQueryset.as_manager()

    def __str__(self):
        return (
            f"id={self.id}, "
            f"ito_id={self.ito_id!r}, "
            f"start_time={self.start_time!s}"
        )

    class Meta:
        ordering = ("start_time",)


class StopPoint(models.Model):
    ito_id = models.TextField(unique=True)
    atco_code = models.CharField(max_length=20)
    is_provisional = models.BooleanField(
        default=False,
        help_text="The stop is provisional and not yet officially in NapTaN",
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10)
    bearing = models.IntegerField()
    geometry = models.PointField()

    def __str__(self):
        return (
            f"id={self.id}, ito_id={self.ito_id!r}, "
            f"name={self.name!r}, atco_code={self.atco_code!r}"
        )

    class Meta:
        ordering = ("atco_code", "is_provisional")
        unique_together = ("atco_code", "is_provisional")
