import csv
import io
import logging
import os
from abc import abstractmethod
from enum import Enum
from zipfile import ZIP_DEFLATED, ZipFile

from django.http.response import FileResponse
from django.views.generic.detail import DetailView
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.data_quality.models.report import PostSchemaViolation
from transit_odp.organisation.models import Dataset

from .constants import (
    ADDITIONAL_SERVICES_PII,
    ERROR_TYPE_PII,
    ERROR_TYPE_SERVICE_CHECK,
    LINK_PII,
    NEXT_STEPS_PII,
    NEXT_STEPS_SERVICE_CHECK,
)

logger = logging.getLogger(__name__)


class PostSchemaErrorType(Enum):
    PII_ERROR = "PII ERROR"
    SERVICE_EXISTS = "SERVICE EXISTS"


class PostSchemaCSV(CSVBuilder):
    """A CSVBuilder class for creating Post Schema CSV strings"""

    def __init__(self, revision):
        self.revision = revision
        self.queryset = self.get_queryset()

    columns = [
        CSVColumn(header="Filename", accessor="filename"),
        CSVColumn(header="Error Type", accessor="error_type"),
        CSVColumn(header="Next Steps", accessor="next_steps"),
        CSVColumn(header="Link to Next Steps Column", accessor="link"),
        CSVColumn(header="Additional Information", accessor="additional_details"),
        CSVColumn(header="Details", accessor="details"),
    ]

    def get_queryset(self):
        return PostSchemaViolation.objects.filter(revision_id=self.revision.id)

    def get_dataset_link(self, dataset_id) -> str:
        """
        Construct a link to the dataset update page
        """
        host = PUBLISH_HOST
        dataset = (
            Dataset.objects.filter(id=dataset_id).values("organisation_id").first()
        )

        if dataset:
            org_id = dataset["organisation_id"]
            return reverse(
                "feed-update", kwargs={"pk1": org_id, "pk": dataset_id}, host=host
            )

        return ""  # Return an empty string if dataset is not found

    def annotate_pii_qs(self, row_data):
        """
        Annotate row when error type is PII
        """
        row_data.update(
            {
                "Error Type": ERROR_TYPE_PII,
                "Next Steps": NEXT_STEPS_PII,
                "Link to Next Steps Column": LINK_PII,
                "Additional Information": ADDITIONAL_SERVICES_PII,
            }
        )
        return row_data

    def annotate_check_service_qs(self, row_data):
        """
        Annotate row when a service exists in a published dataset
        """
        additional_data = row_data.get("Additional Information", {})

        if additional_data:
            published_dataset = additional_data.get("published_dataset")
            service_codes = additional_data.get("service_codes", [])

            row_data.update(
                {
                    "Error Type": ERROR_TYPE_SERVICE_CHECK,
                    "Next Steps": NEXT_STEPS_SERVICE_CHECK,
                    "Link to Next Steps Column": self.get_dataset_link(
                        published_dataset
                    ),
                    "Additional Information": ", ".join(
                        service_codes
                    ),  # Join service codes into a string
                }
            )
        return row_data

    def _create_row(self, obj):
        """
        Convert Django model instance to a dictionary
        """
        row_data = {
            column.header: getattr(obj, column.accessor, None)
            for column in self.columns
        }

        # Convert datetime fields to ISO format
        for key, value in row_data.items():
            if hasattr(value, "isoformat"):
                row_data[key] = value.isoformat()

        return row_data

    def to_string(self):
        """
        Generate CSV as a string
        """
        prefix = f"CSVExporter - to_string - {self.__class__.__name__} - "
        headers = [column.header for column in self.columns]
        rows = [self._create_row(q) for q in self.queryset]

        for row_data in rows:
            details_value = row_data.get("Details", "")

            if details_value == PostSchemaErrorType.PII_ERROR.value:
                row_data = self.annotate_pii_qs(row_data)
            elif details_value == PostSchemaErrorType.SERVICE_EXISTS.value:
                row_data = self.annotate_check_service_qs(row_data)

        cleaned_rows = [
            {k: v for k, v in item.items() if k != "Details"} for item in rows
        ]  # Remove 'Details' rows from the final output
        del headers[-1]  # Remove 'Details' column from the final output

        csvfile = io.StringIO()
        writer = csv.DictWriter(csvfile, fieldnames=headers, quoting=csv.QUOTE_ALL)

        writer.writeheader()
        writer.writerows(cleaned_rows)

        csvfile.seek(0, os.SEEK_END)
        logger.info(prefix + f"Final file size: {csvfile.tell()} bytes.")
        csvfile.seek(0)

        output = csvfile.getvalue()
        csvfile.close()
        logger.info(prefix + "File successfully closed")
        return output


class BasePostSchemaCSVView(DetailView):
    model = Dataset

    @abstractmethod
    def get_revision(self):
        pass

    def render_to_response(self):
        dataset = self.get_object()
        org_id = dataset.organisation_id
        revision = self.get_revision()
        zip_filename = f"validation_{org_id}_{dataset.id}.zip"
        csv_filename = "publisher_errors.csv"

        buffer_ = io.BytesIO()
        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            csv_export = PostSchemaCSV(revision)
            output = csv_export.to_string()
            if csv_export.count() > 0:
                zin.writestr(csv_filename, output)

        buffer_.seek(0)
        response = FileResponse(buffer_)
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response

    def get(self, *args, **kwargs):
        return self.render_to_response()


class ReviewPostSchemaCSVView(BasePostSchemaCSVView):
    def get_revision(self):
        dataset = self.get_object()
        revision = dataset.revisions.get_draft().first()
        return revision
