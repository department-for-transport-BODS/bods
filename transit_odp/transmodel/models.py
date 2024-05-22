from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField

from transit_odp.naptan.models import AdminArea, Locality, StopPoint
from transit_odp.organisation.models import DatasetRevision
from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.transmodel.managers import (
    ServicePatternManager,
    ServicePatternStopManager,
)


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

    txcfileattributes = models.ForeignKey(
        TXCFileAttributes,
        related_name="service_txcfileattributes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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
    line_name = models.CharField(max_length=255, null=True, blank=True)
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

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
        ordering = ("revision", "service_pattern_id", "line_name")

    def __str__(self):
        return f"{self.id}, {self.origin}, {self.destination}"


class VehicleJourney(models.Model):
    start_time = models.TimeField(null=True)
    line_ref = models.CharField(max_length=255, null=True, blank=True)
    journey_code = models.CharField(max_length=255, null=True, blank=True)
    direction = models.CharField(max_length=255, null=True, blank=True)
    departure_day_shift = models.BooleanField(default=False)
    service_pattern = models.ForeignKey(
        ServicePattern,
        on_delete=models.CASCADE,
        related_name="service_pattern_vehicle_journey",
        default=None,
        null=True,
    )
    block_number = models.CharField(max_length=10, null=True, default=None)

    def __str__(self):
        start_time_str = self.start_time.strftime("%H:%M:%S") if self.start_time else ""
        return f"{self.id}, timing_pattern: {self.id}, {start_time_str}"


class StopActivity(models.Model):
    name = models.CharField(max_length=255)
    is_pickup = models.BooleanField(default=False)
    is_setdown = models.BooleanField(default=False)
    is_driverrequest = models.BooleanField(default=False)


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

    stop_activity = models.ForeignKey(
        StopActivity,
        related_name="service_pattern_stops_activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    vehicle_journey = models.ForeignKey(
        VehicleJourney,
        related_name="service_pattern_stops_vehicle_journey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    stop_activity = models.ForeignKey(
        StopActivity,
        related_name="stop_activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    sequence_number = models.IntegerField()

    # Store the atco_code explicitly in case the naptan_stop fails to lookup.
    atco_code = models.CharField(max_length=255)

    txc_common_name = models.CharField(max_length=255, null=True, blank=True)
    departure_time = models.TimeField(null=True, default=None)
    is_timing_point = models.BooleanField(default=False)

    objects = ServicePatternStopManager()

    class Meta:
        ordering = ("service_pattern", "sequence_number")

    def __str__(self):
        return (
            f"{self.id}, {self.atco_code}, service_pattern: {self.service_pattern.id}"
        )


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


class BookingArrangements(models.Model):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name="booking_arrangements"
    )

    description = models.TextField(null=True, blank=True)
    email = models.EmailField(_("email address"), null=True, blank=True)
    phone_number = models.CharField(max_length=16, null=True, blank=True)
    web_address = models.URLField(null=True, blank=True)

    created = CreationDateTimeField(_("created"))
    last_updated = ModificationDateTimeField(_("last_updated"))

    class Meta:
        ordering = ("service_id", "last_updated")
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(email__isnull=False) & ~models.Q(email=""))
                    | (
                        models.Q(phone_number__isnull=False)
                        & ~models.Q(phone_number="")
                    )
                    | (models.Q(web_address__isnull=False) & ~models.Q(web_address=""))
                ),
                name="at_least_one_column_not_empty_or_null",
            )
        ]

    def save(self, *args, **kwargs):
        self.clean()  # validate before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}, service_id: {self.service_id}"


class OperatingProfile(models.Model):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

    DAY_CHOICES = [
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    ]

    vehicle_journey = models.ForeignKey(
        VehicleJourney, on_delete=models.CASCADE, related_name="operating_profiles"
    )

    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)


class NonOperatingDatesExceptions(models.Model):
    vehicle_journey = models.ForeignKey(
        VehicleJourney,
        on_delete=models.CASCADE,
        related_name="non_operating_dates_exceptions",
    )

    non_operating_date = models.DateField(null=True, blank=True)


class OperatingDatesExceptions(models.Model):
    vehicle_journey = models.ForeignKey(
        VehicleJourney,
        on_delete=models.CASCADE,
        related_name="operating_dates_exceptions",
    )

    operating_date = models.DateField(null=True, blank=True)


class FlexibleServiceOperationPeriod(models.Model):
    vehicle_journey = models.ForeignKey(
        VehicleJourney,
        on_delete=models.CASCADE,
        related_name="flexible_service_operation_period",
    )

    start_time = models.TimeField(null=True, blank=True)

    end_time = models.TimeField(null=True, blank=True)


class ServicedOrganisationVehicleJourney(models.Model):
    serviced_organisation = models.ForeignKey(
        "ServicedOrganisations",
        on_delete=models.CASCADE,
        related_name="serviced_organisations",
    )
    vehicle_journey = models.ForeignKey(
        VehicleJourney, on_delete=models.CASCADE, related_name="vehicle_journeys"
    )
    operating_on_working_days = models.BooleanField(default=False)


class ServicedOrganisations(models.Model):
    organisation_code = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)


class ServicedOrganisationWorkingDays(models.Model):
    serviced_organisation_vehicle_journey = models.ForeignKey(
        ServicedOrganisationVehicleJourney,
        on_delete=models.CASCADE,
        related_name="serviced_organisations_vehicle_journey",
        null=True,
        blank=True,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)


class BankHolidays(models.Model):
    txc_element = models.CharField(max_length=255)
    title = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField()
    notes = models.CharField(max_length=255, null=True, blank=True)
    division = models.CharField(max_length=255, null=True, blank=True)
