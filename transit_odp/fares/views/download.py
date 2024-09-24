import io
from abc import abstractmethod
from zipfile import ZIP_DEFLATED, ZipFile

from django.db.models import CharField, Value
from django.http.response import FileResponse
from django.views.generic.detail import DetailView

from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.data_quality.models import SchemaViolation
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.timetable.download import DatasetDownloadView

NETEX_SCHEMA_URL = "http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd"
FARES_URL = "http://naptan.dft.gov.uk/transxchange/schema/schemas.html"
FARES_REF = f"Please refer to the schema document: {NETEX_SCHEMA_URL}"


class DownloadFaresFileView(DatasetDownloadView):
    dataset_type = DatasetType.FARES.value


class FaresSchemaCSV(CSVBuilder):
    """A CSVBuilder class for creating Fares CSV strings"""

    def __init__(self, revision_id: int):
        self._revision_id = revision_id

    columns = [
        CSVColumn(header="Filename", accessor="filename"),
        CSVColumn(header="XML Line Number", accessor="line"),
        CSVColumn(header="Details", accessor="details"),
        CSVColumn(header="Reference", accessor="ref"),
        CSVColumn(header="Important Note", accessor="note"),
    ]

    def get_queryset(self):
        qs = SchemaViolation.objects.filter(revision_id=self._revision_id)
        qs = qs.annotate(note=Value(FARES_URL, output_field=CharField()))
        qs = qs.annotate(ref=Value(FARES_REF, output_field=CharField()))
        return qs


class BaseSchemaViolationsCSVFileView(DetailView):
    model = Dataset

    @abstractmethod
    def get_revision(self):
        pass

    def get(self, *args, **kwargs):
        dataset = self.get_object()
        org_id = dataset.organisation_id
        revision = self.get_revision()

        buffer_ = io.BytesIO()
        zip_filename = f"validation_{org_id}_{dataset.id}.zip"
        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            builder = FaresSchemaCSV(revision_id=revision.id)
            output = builder.to_string()
            if builder.count() > 0:
                zin.writestr("netex_observations.csv", output)

        buffer_.seek(0)
        response = FileResponse(buffer_)
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response


class ReviewSchemaViolationsCSVFileView(BaseSchemaViolationsCSVFileView):
    def get_revision(self):
        dataset = self.get_object()
        revision = dataset.revisions.get_draft().first()
        return revision


class PublishedSchemaViolationsCSVFileView(BaseSchemaViolationsCSVFileView):
    def get_revision(self):
        dataset = self.get_object()
        return dataset.live_revision
