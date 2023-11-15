from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from transit_odp.naptan.models import AdminArea, Locality, StopPoint
from transit_odp.organisation.models import DatasetRevision
from transit_odp.transmodel.managers import (
    ServicePatternManager,
    ServicePatternStopManager,
)

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField


class Service(models.Model):
    revision = models.ForeignKey(
        DatasetRevision, related_name="services", on_delete=models.CASCADE, null=True
    )
    service_code = models.CharField(max_length=255)

    name = models.CharField(max_length=255, blank=True)
    other_names = ArrayField(
        models.CharField(max_length=255, blank=True), blank=True, default=list
    )

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    service_type = models.CharField(max_length=255, default="standard")

    service_patterns = models.ManyToManyField(
        "transmodel.ServicePattern", related_name="services"
    )

    class Meta:
        ordering = ("revision", "service_code")

    def __str__(self):
        return f"{self.id}, {self.name}, {self.service_code}"


class ServicePattern(models.Model):
    service_pattern_id = models.CharField(max_length=255)
    # TODO - remove FK to DatasetRevision. This shouldn't be here
    revision = models.ForeignKey(
        DatasetRevision,
        related_name="service_patterns",
        on_delete=models.CASCADE,
        null=True,
    )
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    stops = models.ManyToManyField(StopPoint, through="transmodel.ServicePatternStop")
    service_links = models.ManyToManyField(
        "transmodel.ServiceLink", related_name="service_patterns"
    )

    admin_areas = models.ManyToManyField(AdminArea, related_name="service_patterns")
    localities = models.ManyToManyField(Locality, related_name="service_patterns")

    geom = models.LineStringField(null=True, blank=True)

    # Get the Localities associated with this ServicePattern

    objects = ServicePatternManager()

    class Meta:
        ordering = ("revision", "service_pattern_id")
        unique_together = ("revision", "service_pattern_id")

    def __str__(self):
        return f"{self.id}, {self.origin}, {self.destination}"


class ServicePatternStop(models.Model):
    service_pattern = models.ForeignKey(
        ServicePattern, on_delete=models.CASCADE, related_name="service_pattern_stops"
    )

    naptan_stop = models.ForeignKey(
        StopPoint,
        related_name="service_pattern_stops",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    sequence_number = models.IntegerField()

    # Store the atco_code explicitly in case the naptan_stop fails to lookup.
    atco_code = models.CharField(max_length=255)

    objects = ServicePatternStopManager()

    class Meta:
        ordering = ("service_pattern", "sequence_number")

    def __str__(self):
        return (
            f"{self.id}, {self.atco_code}, service_pattern: {self.service_pattern.id}"
        )


class TimingPattern(models.Model):
    service_pattern = models.ForeignKey(
        ServicePattern, on_delete=models.CASCADE, related_name="timing_patterns"
    )

    def __str__(self):
        return f"{self.id}, service_pattern: {self.service_pattern.id}"


class TimingPatternStop(models.Model):
    timing_pattern = models.ForeignKey(
        TimingPattern, on_delete=models.CASCADE, related_name="timing_pattern_stops"
    )
    service_pattern_stop = models.ForeignKey(
        ServicePatternStop, on_delete=models.CASCADE, related_name="timings"
    )
    arrival = models.DurationField(
        help_text=(
            "The duration of time from the Vehicle Journey start time "
            "to reach service_pattern_stop"
        )
    )
    departure = models.DurationField(
        help_text=(
            "The duration of time from the Vehicle Journey start "
            "time to depart service_pattern_stop"
        )
    )
    pickup_allowed = models.BooleanField(default=True)
    setdown_allowed = models.BooleanField(default=True)
    timing_point = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id}, {self.timing_pattern.id}, {self.service_pattern_stop.id}"


class ServiceLink(models.Model):
    # Retain the from/to atco codes in case the naptan_stops disappear in a
    # future naptan import.
    from_stop_atco = models.CharField(max_length=255)
    to_stop_atco = models.CharField(max_length=255)

    from_stop = models.ForeignKey(
        StopPoint,
        related_name="from_service_links",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    to_stop = models.ForeignKey(
        StopPoint,
        related_name="to_service_links",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("from_stop_atco", "to_stop_atco")
        unique_together = ("from_stop_atco", "to_stop_atco")

    def __str__(self):
        return f"{self.id}, {self.from_stop_atco} to {self.to_stop_atco}"


class VehicleJourney(models.Model):
    timing_pattern = models.ForeignKey(TimingPattern, on_delete=models.CASCADE)
    start_time = models.TimeField()

    def __str__(self):
        return f"{self.id}, timing_pattern: {self.id}, {self.start_time:%H:%M:%S}"


class BookingArrangements(models.Model):
    service_id = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="booking_arrangements"
    )

    description = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(_("email address"), null=True, blank=True)
    phone_number = models.CharField(max_length=16, null=True, blank=True)
    web_address = models.URLField(null=True, blank=True)

    created = CreationDateTimeField(_("created"))
    last_updated = ModificationDateTimeField(_("last_updated"))

    class Meta:
        ordering = ("service_id", "last_updated")
        # Add a CheckConstraint to ensure at least one of the columns has a value
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(email__isnull=False, email__exact="")
                    | Q(phone_number__isnull=False, phone_number__exact="")
                    | Q(web_address__isnull=False, web_address__exact="")
                ),
                name="at_least_one_column_not_null_or_empty",
            )
        ]

    def __str__(self):
        return f"{self.id}, service_id: {self.service_id}"
