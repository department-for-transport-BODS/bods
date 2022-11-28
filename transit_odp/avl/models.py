from django.core.files.base import ContentFile
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField

from transit_odp.avl.csv.validation import (
    SchemaValidationResponseExporter,
    ValidationReportExporter,
)
from transit_odp.avl.storage import get_sirivm_storage
from transit_odp.avl.validation.models import (
    SchemaValidationResponse,
    ValidationResponse,
)
from transit_odp.common.constants import UTF8
from transit_odp.common.fields import CallableStorageFileField
from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.pipelines.models import TaskResult

limit_to_query = Q(dataset__dataset_type=AVLType) & Q(dataset__live_revision_id=F("id"))


class AVLValidationReport(models.Model):

    revision = models.ForeignKey(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="avl_validation_reports",
        limit_choices_to=limit_to_query,
    )
    critical_count = models.PositiveIntegerField(_("Number of critical issues"))
    non_critical_count = models.PositiveIntegerField(_("Number of non-critical issues"))
    critical_score = models.FloatField(_("Score for critical observations"))
    non_critical_score = models.FloatField(_("Score for non-critical observations"))
    vehicle_activity_count = models.PositiveIntegerField(
        _("Number of VehicleActivity elements tested")
    )

    file = models.FileField(_("AVL validation report file"), null=True)
    created = models.DateField(_("Creation date"))

    def __str__(self):
        return (
            f"id={self.id}, revision_id={self.revision.id}, "
            f"filename={self.file.name!r}, "
            f"critical_count={self.critical_count}, "
            f"non_critical_count={self.non_critical_count}, "
            f"created={self.created.isoformat()}"
        )

    @classmethod
    def from_validation_response(cls, revision_id: int, response: ValidationResponse):
        summary = response.validation_summary
        exporter = ValidationReportExporter(response)
        if response.results:
            file_ = ContentFile(
                exporter.to_csv_string().encode(UTF8), name=exporter.get_filename()
            )
        else:
            file_ = None

        return cls(
            revision_id=revision_id,
            critical_count=summary.critical_error_count,
            non_critical_count=summary.non_critical_error_count,
            critical_score=summary.critical_score,
            non_critical_score=summary.non_critical_score,
            vehicle_activity_count=summary.vehicle_activity_count,
            file=file_,
            created=timezone.now().date(),
        )

    class Meta:
        unique_together = ("revision", "created")


class AVLSchemaValidationReport(models.Model):
    revision = models.ForeignKey(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="avl_schema_validation_reports",
        limit_choices_to=limit_to_query,
    )
    error_count = models.PositiveIntegerField(_("Number of schema errors"))
    file = models.FileField(_("AVL schema validation report file"))
    created = models.DateField(_("Creation date"))

    class Meta:
        unique_together = ("revision", "created")

    def __str__(self):
        return (
            f"id={self.id}, revision_id={self.revision.id}, "
            f"filename={self.file.name!r}, "
            f"error_count={self.error_count}, "
            f"created={self.created.isoformat()}"
        )

    @classmethod
    def from_schema_validation_response(
        cls, revision_id: int, response: SchemaValidationResponse
    ):
        error_count = len(response.errors)
        exporter = SchemaValidationResponseExporter(response)
        file_ = ContentFile(
            exporter.to_csv_string().encode(UTF8), name=exporter.get_filename()
        )
        return cls(
            revision_id=revision_id,
            error_count=error_count,
            file=file_,
            created=timezone.now().date(),
        )


class CAVLValidationTaskResult(TaskResult):
    """This model stores the state of the AVL validation workflow"""

    revision = models.ForeignKey(
        DatasetRevision, related_name="+", on_delete=models.CASCADE
    )

    VALID = "FEED_VALID"
    INVALID = "FEED_INVALID"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    ERROR_CHOICES = [
        (VALID, VALID),
        (INVALID, INVALID),
        (SYSTEM_ERROR, SYSTEM_ERROR),
        (TIMEOUT_ERROR, TIMEOUT_ERROR),
    ]
    result = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        choices=ERROR_CHOICES,
        verbose_name=_("Task Result"),
    )

    def to_valid(self):
        self.result = self.VALID
        self.to_success()

    def to_invalid(self):
        self.result = self.INVALID
        self.to_error()

    def to_system_error(self):
        self.result = self.SYSTEM_ERROR
        self.to_error()

    def to_timeout_error(self):
        self.result = self.TIMEOUT_ERROR
        self.to_error()


class CAVLDataArchive(models.Model):
    SIRIVM = "VM"
    GTFSRT = "RT"
    SIRIVM_TFL = "TL"
    DATA_FORMAT_CHOICES = [
        (SIRIVM, "Siri VM"),
        (GTFSRT, "GTFS RT"),
        (SIRIVM_TFL, "Siri VM TfL"),
    ]

    created = CreationDateTimeField(_("created"))
    last_updated = ModificationDateTimeField(_("last_updated"))
    data = CallableStorageFileField(
        storage=get_sirivm_storage,
        help_text=_("A zip file containing an up to date siri vm XML."),
    )
    data_format = models.CharField(
        max_length=2, choices=DATA_FORMAT_CHOICES, default=SIRIVM
    )

    class Meta:
        get_latest_by = "-created"
        ordering = ("-created",)

    def __repr__(self):

        return (
            f"{self.__class__.__name__}(created={self.created!r}, "
            f"last_updated={self.last_updated!r}, data={self.data.name!r}, "
            f"data_format={self.data_format!r})"
        )


class PPCReportType(models.TextChoices):
    DAILY = ("daily", "daily")
    WEEKLY = ("weekly", "weekly")


class PostPublishingCheckReport(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="ppc_reports",
        limit_choices_to=Q(dataset_type=AVLType),
    )
    created = models.DateField(_("Creation date"))
    granularity = models.CharField(
        _("Daily or weekly"),
        choices=PPCReportType.choices,
        max_length=6,
    )
    file = models.FileField(_("PPC report"))
    vehicle_activities_analysed = models.PositiveIntegerField(
        _("Vehicles analysed"), null=True, blank=True, default=0
    )
    vehicle_activities_completely_matching = models.PositiveIntegerField(
        _("Vehicles completely matching (ex. BlockRef)"),
        null=True,
        blank=True,
        default=0,
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["dataset", "granularity", "created"], name="unique_report"
            )
        ]

    def __str__(self):
        return (
            f"id={self.id}, dataset id={self.dataset.id}, type={self.granularity}, "
            f"created={self.created.isoformat()}, filename={self.file.name!r}, "
            f"vehicle_activities_analysed={self.vehicle_activities_analysed}"
            "vehicle_activities_completely_matching="
            f"{self.vehicle_activities_completely_matching}"
        )
