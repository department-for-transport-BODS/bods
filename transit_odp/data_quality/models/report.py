from django.contrib.postgres.fields import JSONField
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField

from transit_odp.data_quality.models.managers import DataQualityReportManager
from transit_odp.data_quality.pti.models import Violation
from transit_odp.organisation.models import DatasetRevision
from transit_odp.timetables.transxchange import TXCSchemaViolation


class DataQualityReport(models.Model):
    created = CreationDateTimeField(_("created"))
    revision = models.ForeignKey(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="report",
        help_text="Data quality report",
    )
    file = models.FileField(validators=[FileExtensionValidator([".json"])])

    class Meta:
        get_latest_by = "created"
        ordering = ("-created",)

    def __str__(self):
        return (
            f"DataQualityReport("
            f"id={self.id}, "
            f"created={self.created.isoformat()}, "
            f"revision={self.revision_id}, "
            f"file={self.file.name})"
        )

    objects = DataQualityReportManager()


class DataQualityReportSummary(models.Model):
    report = models.OneToOneField(
        "data_quality.DataQualityReport",
        on_delete=models.CASCADE,
        related_name="summary",
    )
    data = JSONField()

    def __str__(self):
        return (
            f"DataQualityReportSummary("
            f"id={self.id}, "
            f"report={self.report_id}, "
            f"data={self.data})"
        )


class PTIObservation(models.Model):
    revision = models.ForeignKey(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="pti_observations",
        help_text=_("The revision that observation occurred in."),
    )
    filename = models.CharField(
        max_length=256, help_text=_("The name of the file the observation occurs in.")
    )
    line = models.IntegerField(help_text=_("The line number of the observation."))
    details = models.CharField(
        max_length=1024, help_text=_("Details of the observation.")
    )
    element = models.CharField(
        max_length=256, help_text=_("The element which generated the observation.")
    )
    category = models.CharField(
        max_length=1024, help_text=_("The category of the observation.")
    )
    reference = models.CharField(
        max_length=64,
        help_text=_("The section that details this observation."),
        default="0.0",
    )
    created = CreationDateTimeField(_("DateTime observation was created."))

    def __str__(self):
        return (
            f"revision_id={self.revision.id}, filename={self.filename!r}, "
            f"line={self.line}, category={self.category!r}, "
            f"created={self.created:%Y-%m-%d %H:%M:%S}"
        )

    @classmethod
    def from_violation(cls, revision_id: int, violation: Violation):
        return cls(
            revision_id=revision_id,
            line=violation.line,
            filename=violation.filename,
            element=violation.name,
            details=violation.observation.details,
            category=violation.observation.category,
            reference=violation.observation.reference,
        )


class SchemaViolation(models.Model):
    revision = models.ForeignKey(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="schema_violations",
        help_text=_("The revision that observation occurred in."),
    )
    filename = models.CharField(
        max_length=256, help_text=_("The name of the file the observation occurs in.")
    )
    line = models.IntegerField(help_text=_("The line number of the observation."))
    details = models.CharField(
        max_length=1024, help_text=_("Details of the observation.")
    )
    created = CreationDateTimeField(_("DateTime observation was created."))

    def __str__(self):
        return (
            f"revision_id={self.revision.id}, filename={self.filename!r}, "
            f"line={self.line}, "
            f"created={self.created:%Y-%m-%d %H:%M:%S}"
        )

    @classmethod
    def from_violation(cls, revision_id: int, violation: TXCSchemaViolation):
        return cls(
            revision_id=revision_id,
            filename=violation.filename,
            line=violation.line,
            details=violation.details,
        )
