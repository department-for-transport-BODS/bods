import io
from abc import abstractmethod
from zipfile import ZIP_DEFLATED, ZipFile

from django.db.models import CharField, Value
from django.db.models.expressions import Case, When
from django.db.models.functions import Concat
from django.http.response import FileResponse
from django.views.generic.detail import DetailView

from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.data_quality.models import PTIObservation, SchemaViolation
from transit_odp.data_quality.pti.constants import (
    NO_REF,
    REF_PREFIX,
    REF_SUFFIX,
    REF_URL,
    get_important_note,
)
from transit_odp.organisation.models import Dataset
from transit_odp.timetables.views.post_schema import PostSchemaCSV

TXC_NOTE = (
    "You need to update your data to 2.4 TxC schema in order to upload data to BODS."
)
TXC_URL = "http://naptan.dft.gov.uk/transxchange/schema/schemas.html"
TXC_REF = f"Please refer to the 2.4 TxC schema document: {TXC_URL}"


class TXCSchemaCSV(CSVBuilder):
    """A CSVBuilder class for creating TXC CSV strings"""

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
        qs = qs.annotate(note=Value(TXC_NOTE, output_field=CharField()))
        qs = qs.annotate(ref=Value(TXC_REF, output_field=CharField()))
        return qs


class PTICSV(CSVBuilder):
    """A CSVBuilder class for creating PTI CSV strings"""

    def __init__(self, revision_id: int):
        self._revision_id = revision_id

    columns = [
        CSVColumn(header="Filename", accessor="filename"),
        CSVColumn(header="XML Line Number", accessor="line"),
        CSVColumn(header="XML Element", accessor="element"),
        CSVColumn(
            header="Category",
            accessor="category",
        ),
        CSVColumn(header="Details", accessor="details"),
        CSVColumn(header="Reference", accessor="complete_ref"),
        CSVColumn(header="Important Note", accessor="note"),
    ]

    def get_queryset(self):
        qs = PTIObservation.objects.filter(revision_id=self._revision_id)
        qs = qs.annotate(note=Value(get_important_note(), output_field=CharField()))
        section_ref = Concat(
            Value(REF_PREFIX, output_field=CharField()),
            "reference",
            Value(REF_SUFFIX, output_field=CharField()),
            Value(REF_URL, output_field=CharField()),
            output_field=CharField(),
        )
        general_ref = Concat(
            Value(NO_REF, output_field=CharField()),
            Value(REF_URL, output_field=CharField()),
            output_field=CharField(),
        )
        case = Case(When(reference="0", then=general_ref), default=section_ref)
        qs = qs.annotate(complete_ref=case)
        return qs


class BaseViolationsCSVFileView(DetailView):
    """
    Download the pti observations csv file.
    """

    model = Dataset

    @abstractmethod
    def get_revision(self):
        pass

    def render_all_violations(self, *args, **kwargs):
        dataset = self.get_object()
        org_id = dataset.organisation_id
        revision = self.get_revision()
        buffer_ = io.BytesIO()
        zip_filename = f"validation_{org_id}_{dataset.id}.zip"

        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            if revision.schema_violations.count() > 0:
                builder = TXCSchemaCSV(revision_id=revision.id)
                output = builder.to_string()
                if builder.count() > 0:
                    zin.writestr("txc_observations.csv", output)

            if revision.post_schema_violations.count() > 0:
                csv_export = PostSchemaCSV(revision)
                output = csv_export.to_string()
                csv_filename = "publisher_errors.csv"
                if csv_export.count() > 0:
                    zin.writestr(csv_filename, output)

            if revision.pti_observations.count() > 0:
                pti_report_filename = (
                    f"BODS_TXC_validation_{revision.dataset.organisation.name}"
                    f"_{revision.dataset_id}"
                    f"_{revision.pti_observations.last().created:%H:%M_%d%m%Y}.csv"
                )
                builder = PTICSV(revision_id=revision.id)
                output = builder.to_string()
                if builder.count() > 0:
                    zin.writestr(pti_report_filename, output)

        buffer_.seek(0)
        response = FileResponse(buffer_)
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response

    def render_to_response(self, *args, **kwargs):
        return self.render_all_violations(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.render_to_response()


class ReviewViolationsCSVFileView(BaseViolationsCSVFileView):
    def get_revision(self):
        dataset = self.get_object()
        revision = dataset.revisions.get_draft().first()
        return revision


class PublishedViolationsCSVFileView(BaseViolationsCSVFileView):
    def get_revision(self):
        dataset = self.get_object()
        return dataset.live_revision
