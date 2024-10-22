from django.contrib.gis.db import models

from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField
from django.utils.timezone import now

from transit_odp.organisation.models.data import DatasetRevision
from transit_odp.transmodel.models import (
    ServicePatternStop,
    VehicleJourney,
    ServicedOrganisations,
)
from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.dqs.querysets import TaskResultsQueryset, ObservationResultsQueryset
from transit_odp.dqs.constants import ReportStatus, TaskResultsStatus

BATCH_SIZE = 1000


class Report(models.Model):
    created = CreationDateTimeField(_("created"))
    file_name = models.CharField(blank=True, max_length=255)
    revision = models.ForeignKey(
        DatasetRevision, related_name="dqs_report", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=64, null=True)

    class Meta:
        get_latest_by = "created"

    @classmethod
    def initialise_dqs_task(cls, revision: object) -> object:
        """
        Create a new Report instance with the provided data and save it to the database.
        """
        existing_report = cls.objects.filter(revision=revision).first()
        if existing_report:
            existing_report.created = now()
            existing_report.file_name = ""
            existing_report.status = ReportStatus.PIPELINE_PENDING.value
            existing_report.save()
            return existing_report

        new_report = cls(
            file_name="", revision=revision, status=ReportStatus.PIPELINE_PENDING.value
        )
        new_report.save()
        return new_report


class Checks(models.Model):
    observation = models.CharField(max_length=1024)
    importance = models.CharField(max_length=64)
    category = models.CharField(max_length=64)
    queue_name = models.CharField(max_length=256, blank=True, null=True)

    @classmethod
    def get_all_checks(cls) -> object:
        """
        Fetches all checks in the database
        """
        return cls.objects.all()


class TaskResults(models.Model):
    created = CreationDateTimeField(_("created"))
    modified = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=64)
    message = models.TextField(
        blank=True, help_text="Contains more details about the error"
    )
    checks = models.ForeignKey(
        Checks,
        related_name="dqs_taskresults_check",
        on_delete=models.SET_NULL,
        null=True,
    )
    dataquality_report = models.ForeignKey(
        Report,
        related_name="dqs_taskresults_report",
        on_delete=models.CASCADE,
        null=True,
    )
    transmodel_txcfileattributes = models.ForeignKey(
        TXCFileAttributes,
        related_name="dqs_taskresults_txcfileattributes",
        on_delete=models.CASCADE,
        null=True,
    )

    objects = TaskResultsQueryset.as_manager()

    @classmethod
    def initialize_task_results(cls, report: object, combinations: object) -> object:
        """
        Create a TaskResults object based on the given revision, TXCFileAttribute,
        and Check objects.
        """
        task_results_to_create = []
        for txc_file_attribute, check in combinations:
            task_result = cls(
                status=TaskResultsStatus.PENDING.value,
                message="",
                checks=check,
                dataquality_report=report,
                transmodel_txcfileattributes=txc_file_attribute,
            )
            task_results_to_create.append(task_result)

        return cls.objects.bulk_create(task_results_to_create, batch_size=BATCH_SIZE)


class ObservationResults(models.Model):
    details = models.TextField(
        blank=True, help_text="Contains more details about the error"
    )

    is_suppressed = models.BooleanField(
        default=None,
        help_text="Contains whether the observation result is suppressed",
        null=True,
        blank=True,
    )
    serviced_organisation_id = models.ForeignKey(
        ServicedOrganisations,
        default=None,
        help_text="Contains the link to serviced organisation id",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    taskresults = models.ForeignKey(
        TaskResults,
        related_name="dqs_observationresult_taskresults",
        on_delete=models.CASCADE,
    )
    vehicle_journey = models.ForeignKey(
        VehicleJourney,
        on_delete=models.CASCADE,
        related_name="dqs_observationresult_vehicle_journey",
        null=True,
    )

    service_pattern_stop = models.ForeignKey(
        ServicePatternStop,
        on_delete=models.CASCADE,
        related_name="dqs_observationresult_service_pattern_stop",
        null=True,
    )

    objects = ObservationResultsQueryset.as_manager()
