from typing import List, Optional

from django.core.files.base import File
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import JSONField, Q
from django.http.response import FileResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField

from transit_odp.data_quality.dataclasses import Report
from transit_odp.data_quality.models.managers import DataQualityReportManager
from transit_odp.data_quality.pti.models import Violation
from transit_odp.data_quality.pti.report import PTIReport
from transit_odp.organisation.models import DatasetRevision
from transit_odp.timetables.transxchange import TXCSchemaViolation


class DataQualityReport(models.Model):
    score = models.FloatField(_("Data quality score"), default=0.0)
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
        constraints = [
            models.CheckConstraint(
                name="dq_score_must_be_between_0_and_1",
                check=Q(score__gte=0.0) & Q(score__lte=1.0),
            )
        ]

    def __str__(self):
        return (
            f"DataQualityReport("
            f"id={self.id}, "
            f"created={self.created.isoformat()}, "
            f"revision={self.revision_id}, "
            f"file={self.file.name})"
        )

    def to_report(self):
        """
        Returns a pure python Report object.
        """
        return Report(self.file)

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


class PTIValidationResult(models.Model):
    revision = models.OneToOneField(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="pti_result",
        help_text=_("The revision being validated."),
    )
    count = models.IntegerField(help_text=_("Number of PTI violations."))
    report = models.FileField(validators=[FileExtensionValidator([".zip"])])
    created = CreationDateTimeField(_("created"))

    @property
    def is_compliant(self):
        return self.count == 0

    def to_http_response(self) -> Optional[FileResponse]:
        org_id = self.revision.dataset.organisation_id
        zip_filename = f"validation_{org_id}_{self.revision.dataset_id}.zip"
        self.report.seek(0)
        response = FileResponse(self.report.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response

    @classmethod
    def from_pti_violations(
        cls, revision: DatasetRevision, violations: List[Violation]
    ):
        """
        Creates a PTIValidationResult from a DatasetRevision and a list of Violations.

        Args:
            revision (DatasetRevision): The revision containing the violations.
            violations (List[Violation]): The violations that a revision has.
        """
        now = timezone.now()
        pti_report_filename = (
            f"BODS_TXC_validation_{revision.dataset.organisation.name}"
            f"_{revision.dataset_id}"
            f"_{now:%H_%M_%d%m%Y}.csv"
        )
        results = PTIReport(filename=pti_report_filename)
        for violation in violations:
            results.write_violation(violation=violation)

        zip_filename = f"pti_validation_revision_{revision.id}.zip"
        report = File(results.to_zip_as_bytes(), name=zip_filename)
        return cls(revision_id=revision.id, count=len(violations), report=report)


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
