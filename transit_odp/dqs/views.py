from django.shortcuts import render
from django.views.generic import DetailView
from waffle import flag_is_active
from transit_odp.dqs.models import Report
from transit_odp.data_quality.report_summary import Summary
# Create your views here.


class ReportOverviewView(DetailView):
    template_name = "data_quality/report.html"
    pk_url_kwarg = "report_id"
    model = Report 
    def get_queryset(self):
        dataset_id = self.kwargs["pk"]
        result = (
            super()
            .get_queryset()
            .filter(revision__dataset_id=dataset_id)
            .filter(id=self.kwargs["report_id"])
            .filter(status="PIPELINE_SUCCEDED")
            .select_related("revision")
        )
        return result

    def get_context_data(self, **kwargs):
        revision_id = None
        context = super().get_context_data(**kwargs)
        if kwargs.get("object"):
            revision_id = kwargs.get("object").revision_id

        report = (
            Report.objects.filter(revision_id=revision_id)
            .filter(status="PIPELINE_SUCCEDED")
            .order_by("-created")
            .first()
        )
        report_id = report.id if report else None

        summary = Summary.get_report(report_id, revision_id)

        context.update(
            {
                "title": report.revision.name,
                "warning_data": summary.data,
                "total_warnings": summary.count,
                "bus_services_affected": summary.bus_services_affected,
                "is_new_data_quality_service_active": self.is_new_data_quality_service_active,
            }
        )
        return context