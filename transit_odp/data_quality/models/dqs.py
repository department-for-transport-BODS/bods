from django.contrib.gis.db import models

from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField

from transit_odp.organisation.models.data import DatasetRevision
from transit_odp.transmodel.models import ServicePatternStop, VehicleJourney

class Report(models.Model):
    created = CreationDateTimeField(_("created"))
    file_name = models.CharField(blank=True, max_length=255)
    revision = models.ForeignKey(
        DatasetRevision, related_name="dqs_report", on_delete=models.CASCADE
    )

class Checks(models.Model):
    observation = models.CharField(max_length=1024)
    importance = models.CharField(max_length=64)
    category = models.CharField(max_length=64)

class TaskResults(models.Model):
    created = CreationDateTimeField(_("created"))
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=64)
    message = models.TextField(
        blank=True, help_text="Contains more details about the error"
    )
    checks = models.ForeignKey(
        Checks, related_name="dqs_taskresults_check", on_delete=models.SET_NULL, null=True
    )

class ErrorResults(models.Model):
    details = models.TextField(
        blank=True, help_text="Contains more details about the error"
    )
    taskresults = models.ForeignKey(
        TaskResults, related_name="dqs_errorresult_taskresults", on_delete=models.CASCADE
    )
    vehicle_journey = models.ForeignKey(
        VehicleJourney, on_delete=models.CASCADE, related_name="dqs_errorresult_vehicle_journey"
    )

    service_pattern_stop = models.ForeignKey(
        ServicePatternStop, on_delete=models.CASCADE, related_name="dqs_errorresult_service_pattern_stop"
    )