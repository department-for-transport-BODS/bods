import io
from collections import namedtuple
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.views.generic import TemplateView, View

from transit_odp.site_admin.exports import (
    AgentUserCSV,
    APIRequestCSV,
    ConsumerCSV,
    DailyConsumerRequestCSV,
    OperationalStatsCSV,
    OrganisationCSV,
    PublisherCSV,
    RawConsumerRequestCSV,
)
from transit_odp.users.views.mixins import SiteAdminViewMixin

__all__ = ["MetricsDownloadView", "OperationalMetricsFileView", "APIMetricsFileView"]

CSVFile = namedtuple("CSVFile", "name,builder_class")
User = get_user_model()


class MetricsDownloadView(SiteAdminViewMixin, TemplateView):
    template_name = "site_admin/metrics/download.html"


class OperationalMetricsFileView(SiteAdminViewMixin, View):
    """ A view for downloading BODS operational metrics zip file."""

    def render_to_response(self, *args, **kwargs):
        filename = "operationalexports.zip"
        buffer_ = io.BytesIO()
        files = (
            CSVFile("organisations.csv", OrganisationCSV),
            CSVFile("publishers.csv", PublisherCSV),
            CSVFile("consumers.csv", ConsumerCSV),
            CSVFile("stats.csv", OperationalStatsCSV),
            CSVFile("agents.csv", AgentUserCSV),
        )

        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            for file_ in files:
                Builder = file_.builder_class
                zin.writestr(file_.name, Builder().to_string())

        buffer_.seek(0)
        response = FileResponse(buffer_)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    def get(self, *args, **kwargs):
        return self.render_to_response()


class APIMetricsFileView(SiteAdminViewMixin, View):
    """ A view downloading BODS API usage metrics zip file."""

    def render_to_response(self, *args, **kwargs):
        filename = "apimetrics.zip"
        buffer_ = io.BytesIO()
        files = [
            CSVFile("dailyaggregates.csv", APIRequestCSV),
            CSVFile("dailyconsumerbreakdown.csv", DailyConsumerRequestCSV),
            CSVFile("rawapimetrics.csv", RawConsumerRequestCSV),
        ]

        with ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
            for file_ in files:
                Builder = file_.builder_class
                zin.writestr(file_.name, Builder().to_string())

        buffer_.seek(0)
        response = FileResponse(buffer_)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    def get(self, *args, **kwargs):
        return self.render_to_response(*args, **kwargs)
