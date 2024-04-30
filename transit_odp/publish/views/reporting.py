import io
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views import View
from django.views.generic import DetailView

from transit_odp.organisation.csv.consumer_feedback import ConsumerFeedbackCSV
from transit_odp.organisation.csv.consumer_interactions import CSV_HEADERS
from transit_odp.organisation.models import Organisation
from transit_odp.publish.constants import INTERACTIONS_DEFINITION

ASSETS = Path(__file__).parents[2] / Path("organisation", "csv", "assets")

FEEDBACK_DEFINITION = "feedbackreportingoperatorbreakdown.txt"


class ConsumerFeedbackView(View):
    organisation = None
    add_name_email_columns = False

    def get(self, *args, **kwargs):
        self.organisation = get_object_or_404(Organisation, id=self.kwargs["pk1"])
        if self.request.user.is_authenticated:
            self.add_name_email_columns = (
                self.organisation in self.request.user.organisations.all()
            )
        return self.render_to_response()

    def render_to_response(self, *args, **kwargs):
        organisation_id = self.kwargs["pk1"]
        buffer_ = io.BytesIO()
        common_name = f"Feedbackreport_{self.organisation.name}_{now():%d%m%y}"
        zip_filename = f"{common_name}.zip"
        csv_filename = f"{common_name}.csv"

        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            builder = ConsumerFeedbackCSV(
                organisation_id=organisation_id,
                add_name_email_columns=self.add_name_email_columns,
            )
            output = builder.to_string()
            if builder.count() > 0:
                zin.writestr(csv_filename, output)
                zin.write(ASSETS / FEEDBACK_DEFINITION, FEEDBACK_DEFINITION)

        buffer_.seek(0)
        response = FileResponse(buffer_)
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response


class ConsumerInteractionsView(DetailView):
    model = Organisation
    pk_url_kwarg = "pk1"

    def get_queryset(self):
        return super().get_queryset().select_related("stats")

    def render_empty_response(self):
        basename = f"Consumer_metrics_{self.object.name}_{now():%d%m%y}"
        buffer_ = io.BytesIO()
        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            zin.writestr(basename + ".csv", ",".join(CSV_HEADERS))
            zin.write(ASSETS / INTERACTIONS_DEFINITION, INTERACTIONS_DEFINITION)

        buffer_.seek(0)
        response = FileResponse(buffer_)
        zip_filename = basename + ".zip"
        response["Content-Disposition"] = f"attachment; filename={zip_filename}"
        return response

    def render_to_response(self, *args, **kwargs):
        monthly_breakdown = self.object.stats.monthly_breakdown
        if not monthly_breakdown:
            return self.render_empty_response()

        response = FileResponse(monthly_breakdown)
        response[
            "Content-Disposition"
        ] = f"attachment; filename={monthly_breakdown.name}"
        return response
