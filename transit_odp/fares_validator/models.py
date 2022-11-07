from typing import List, Optional

from django.core.files.base import File
from django.core.validators import FileExtensionValidator
from django.db import models
from django.http.response import FileResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField

from transit_odp.fares_validator.types import Violation
from transit_odp.fares_validator.views.export_excel import FaresXmlExporter
from transit_odp.organisation.models import DatasetRevision

type_of_observation = "Simple fares validation failure"
category = ""  # Itr2 To be extratced from the xml path


class FaresValidationResult(models.Model):
    revision = models.OneToOneField(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="fares_validation_result",
        help_text=_("The revision being validated."),
    )
    count = models.IntegerField(help_text=_("Number of fare violations."))
    report = models.FileField(validators=[FileExtensionValidator([".xlsx"])])
    created = CreationDateTimeField(_("created"))

    @property
    def is_compliant(self):
        return self.count == 0

    def to_http_response(self) -> Optional[FileResponse]:
        self.report.seek(0)
        response = FileResponse(self.report.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={self.report}"
        return response

    @classmethod
    def save_validation_result(
        cls, revision_id: int, org_id: int, violations: List[Violation]
    ):
        """
        Creates a PTIValidationResult from a DatasetRevision and a list of Violations.

        Args:
            revision (DatasetRevision): The revision containing the violations.
            violations (List[Violation]): The violations that a revision has.
        """
        now = timezone.now()
        fares_validator_report_name = (
            f"BODS_Fares_Validation_{org_id}_{revision_id}_{now:%H_%M_%d%m%Y}.xlsx"
        )
        results = FaresXmlExporter(
            revision_id, org_id, fares_validator_report_name, violations
        )
        report = File(results, name=fares_validator_report_name)
        return cls(revision_id=revision_id, count=len(violations), report=report)


class FaresValidation(models.Model):
    revision = models.ForeignKey(
        DatasetRevision,
        on_delete=models.CASCADE,
        related_name="fares_validations",
        help_text=_("The revision that validation occurred in."),
    )
    organisation = models.ForeignKey(
        "organisation.Organisation",
        on_delete=models.CASCADE,
        help_text="Bus portal organisation.",
    )
    file_name = models.CharField(
        max_length=256, help_text=_("The name of the file the observation occurs in.")
    )
    error_line_no = models.IntegerField(
        help_text=_("The line number of the observation.")
    )
    type_of_observation = models.CharField(
        max_length=1024, help_text=_("Type Of Observation")
    )
    category = models.CharField(
        max_length=1024, help_text=_("The category of the observation.")
    )
    error = models.CharField(
        max_length=2000, help_text=_("The detailed error of the observation.")
    )
    reference = models.CharField(
        max_length=1024,
        default="Please see BODS Fares Validator Guidance v0.2",
        help_text=_("The referenc of the observation"),
    )
    important_note = models.CharField(
        max_length=2000,
        default="Data containing this warning will be rejected by BODS after January 2023. Please contact your ticket machine supplier",
        help_text=_("The Important Note error of the observation."),
    )

    def __str__(self):
        return "%s %s %s" % (self.file_name, self.dataset_id, self.organisation)

    @classmethod
    def save_observations(cls, revision_id: int, org_id: int, violation: Violation):
        return cls(
            revision_id=revision_id,
            organisation_id=org_id,
            file_name=violation.filename,
            error_line_no=violation.line,
            error=violation.observation.details,
            type_of_observation=violation.observation.category,
            category=category,
        )
