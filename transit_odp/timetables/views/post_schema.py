import csv
import io
import logging
import os
import re
from abc import abstractmethod
from zipfile import ZIP_DEFLATED, ZipFile

from django.http.response import FileResponse
from django.views.generic.detail import DetailView
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.data_quality.models.report import PostSchemaViolation
from transit_odp.organisation.models import Dataset

logger = logging.getLogger(__name__)

ERROR_TYPE = "Your TransXchange contains personal identifiable information"
NEXT_STEPS = "Please download the new transXchange tool here"
LINK = "https://www.gov.uk/guidance/publish-bus-open-data#publishing-your-bus-data"
ADDITIONAL_SERVICES = "The Help Desk can be contacted by telephone or email as follows.\n\nTelephone: +44 (0) 800 028 0930\nEmail: bodshelpdesk@kpmg.co.uk"


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
        CSVColumn(header="Additional Information", accessor="additional_information"),
        CSVColumn(header="Details", accessor="details"),
    ]

    def get_queryset(self):
        return PostSchemaViolation.objects.filter(revision_id=self.revision.id)

    def get_dataset_link(self, dataset_id) -> str:
        """
        Construct a link to the dataset update page
        """
        host = PUBLISH_HOST
        dataset = Dataset.objects.filter(id=dataset_id).values("organisation_id")
        org_id = dataset[0]["organisation_id"]

        dataset_url = reverse(
            "feed-update", kwargs={"pk1": org_id, "pk": dataset_id}, host=host
        )
        return dataset_url

    def annotate_pii_qs(self, row):
        """
        Create row when error type is PII
        """
        row[1:5] = [ERROR_TYPE, NEXT_STEPS, LINK, ADDITIONAL_SERVICES]
        return row

    def annotate_check_service_qs(self, row):
        """
        Create row when a service exists in published dataset
        """
        data = row[-1]
        published_dataset = self.extract_value(data, r"PUBLISHED_DATASET:(\d+)")
        dataset_link = self.get_dataset_link(published_dataset)

        service_codes = self.extract_service_codes(data)

        row[1:5] = [
            "Attempted to publish for a service that is already in an active dataset",
            "Click the supplied link to update your dataset",
            dataset_link,
            service_codes,
        ]
        return row

    @staticmethod
    def extract_value(data, pattern):
        match = re.search(pattern, data)
        return match.group(1) if match else None

    @staticmethod
    def extract_service_codes(data):
        match = re.search(r"SERVICE_CODES:\['(.*?)'\]", data)
        if match:
            return ", ".join(match.group(1).replace("'", "").split(", "))
        return ""

    def to_string(self):
        prefix = f"CSVExporter - to_string - {self.__class__.__name__} - "
        headers = [column.header for column in self.columns]
        rows = [self._create_row(q) for q in self.queryset]

        for i, row in enumerate(rows):
            rows[i] = (
                self.annotate_pii_qs(row)
                if row[-1] == "PII ERROR"
                else self.annotate_check_service_qs(row)
            )
            del row[-1]

        csvfile = io.StringIO()
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(rows)

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
