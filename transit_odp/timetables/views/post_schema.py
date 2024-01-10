import io
from abc import abstractmethod
from zipfile import ZIP_DEFLATED, ZipFile

from django.db.models import CharField, Value
from django.http.response import FileResponse
from django.views.generic.detail import DetailView

from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.data_quality.models.report import PostSchemaViolation
from transit_odp.organisation.models import Dataset

ERROR_TYPE = "Your TransXchange contains personal identifiable information"
NEXT_STEPS = "Please download the new transXchange tool here"
LINK = "https://www.gov.uk/guidance/publish-bus-open-data#publishing-your-bus-data"
ADDITIONAL_SERVICES = "The Help Desk can be contacted by telephone or email as follows.\n\nTelephone: +44 (0) 800 028 0930\nEmail: bodshelpdesk@kpmg.co.uk"


class PostSchemaCSV(CSVBuilder):
    """A CSVBuilder class for creating Post Schema CSV strings"""

    def __init__(self, revision):
        self.revision = revision

    columns = [
        CSVColumn(header="Error Type", accessor="error_type"),
        CSVColumn(header="Next Steps", accessor="next_steps"),
        CSVColumn(header="Link to Next Steps Column", accessor="link"),
        CSVColumn(header="Additional Information", accessor="additional_information"),
    ]

    def get_queryset(self):
        qs = PostSchemaViolation.objects.filter(revision_id=self.revision.id)
        qs = qs.annotate(
            error_type=Value(ERROR_TYPE, output_field=CharField()),
            next_steps=Value(NEXT_STEPS, output_field=CharField()),
            link=Value(LINK, output_field=CharField()),
            additional_information=Value(ADDITIONAL_SERVICES, output_field=CharField()),
        )

        return qs


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
