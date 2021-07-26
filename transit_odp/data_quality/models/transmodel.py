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
from django.contrib.gis.geos import LineString, Point
from django.contrib.postgres.fields import ArrayField
from django.db.models import DateField

from transit_odp.data_quality.dataclasses import features
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
    def from_feature(cls, line: features.Line):
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

    @classmethod
    def from_feature(cls, feature: features.ServicePattern, service_id: int):
        geometry = LineString(*feature.geometry.coordinates, srid=4326)
        return cls(
            ito_id=feature.id,
            service_id=service_id,
            name=feature.properties.feature_name,
            geometry=geometry,
        )


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
            f"service_pattern_id={self.service_pattern_id}, "
            f"position={self.position}, "
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
            f"id={self.id}, "
            f"service_pattern_id={self.service_pattern_id}, "
            f"service_link_id={self.service_link_id}, "
            f"position={self.position}"
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
            f"service_pattern_id={self.service_pattern_id}"
        )

    @classmethod
    def from_feature(cls, feature: features.TimingPattern, service_pattern_id: int):
        return cls(ito_id=feature.id, service_pattern_id=service_pattern_id)


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
            f"timing_pattern_id={self.timing_pattern_id}, "
            f"service_pattern_stop_id={self.service_pattern_stop_id}"
        )

    @classmethod
    def from_feature(
        cls,
        feature: features.Timing,
        timing_pattern_id: int,
        service_pattern_stop_id: int,
    ):
        return TimingPatternStop(
            timing_pattern_id=timing_pattern_id,
            service_pattern_stop_id=service_pattern_stop_id,
            arrival=feature.arrival,
            departure=feature.departure,
            pickup_allowed=feature.pickup_allowed,
            setdown_allowed=feature.setdown_allowed,
            timing_point=feature.timing_point,
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

    @classmethod
    def from_feature(
        cls, feature: features.ServiceLink, from_stop_id: int, to_stop_id: int
    ):
        geometry = LineString(*feature.geometry.coordinates, srid=4326)
        return cls(
            ito_id=feature.id,
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
            geometry=geometry,
        )


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

    @classmethod
    def from_feature(cls, feature: features.VehicleJourney, timing_pattern_id: int):
        return cls(
            ito_id=feature.id,
            timing_pattern_id=timing_pattern_id,
            start_time=feature.start_time,
            dates=feature.datetime_dates,
        )


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
        unique_together = ("ito_id", "atco_code", "is_provisional")

    @classmethod
    def from_feature(cls, stop: features.Stop):
        geometry = Point(*stop.geometry.coordinates, srid=4326)
        return cls(
            ito_id=stop.id,
            atco_code=stop.properties.atco_code,
            is_provisional=stop.properties.synthetic,
            name=stop.properties.feature_name,
            type=stop.properties.type,
            bearing=stop.properties.bearing,
            geometry=geometry,
        )
