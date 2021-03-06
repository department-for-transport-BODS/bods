from django.http.response import Http404, HttpResponse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.base import RedirectView, View

from transit_odp.data_quality.constants import OBSERVATIONS
from transit_odp.data_quality.csv import ObservationCSV
from transit_odp.data_quality.models import DataQualityReport
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.users.views.mixins import OrgUserViewMixin

from ..report_summary import Summary
from .mixins import WithDraftRevision


class DraftReportOverviewView(OrgUserViewMixin, RedirectView, WithDraftRevision):
    permanent = False
    query_string = False
    pattern_name = "dq:overview"

    def get_latest_report(self):
        revision_id = self.get_revision_id()
        try:
            report = DataQualityReport.objects.filter(revision_id=revision_id).latest()
        except DataQualityReport.DoesNotExist:
            raise Http404
        else:
            return report

    def get_redirect_url(self, *args, **kwargs):
        report = self.get_latest_report()
        kwargs["report_id"] = report.id
        return super().get_redirect_url(*args, **kwargs)


class ReportOverviewView(DetailView):
    template_name = "data_quality/report.html"
    pk_url_kwarg = "report_id"
    model = DataQualityReport

    def get_queryset(self):
        dataset_id = self.kwargs["pk"]
        return (
            super()
            .get_queryset()
            .add_number_of_lines()
            .filter(revision__dataset_id=dataset_id)
            .select_related("summary")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        summary = Summary.from_report_summary(report.summary)
        rag = get_data_quality_rag(report)
        context.update(
            {
                "title": report.revision.name,
                "warning_data": summary.data,
                "total_warnings": summary.count,
                "dq_score": rag,
            }
        )
        return context


class ReportCSVDownloadView(View):
    model = DataQualityReport
    pk_url_kwarg = "report_id"

    def get_queryset(self):
        dataset_id = self.kwargs["pk"]
        return super().get_queryset().filter(revision__dataset_id=dataset_id)

    def render_to_response(self, *args, **kwargs):
        dataset_id = self.kwargs.get("pk")
        report_id = self.kwargs.get("report_id")
        now = timezone.now()
        filename = f"{now:%Y-%m-%d_%H%M%S}_ID{dataset_id}.csv"
        observations = ObservationCSV(report_id, observations=OBSERVATIONS)
        file_ = observations.to_csv()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    def get(self, *args, **kwargs):
        return self.render_to_response(*args, **kwargs)
