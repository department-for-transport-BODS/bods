from django.views.generic.detail import DetailView
from django_hosts import reverse

import config
from transit_odp.data_quality.constants import ExpiredLines, MissingBlockNumber
from transit_odp.data_quality.models.warnings import (
    LineExpiredWarning,
    LineMissingBlockIDWarning,
)
from transit_odp.data_quality.tables.base import JourneyLineListTable
from transit_odp.data_quality.tables.lines import (
    LineExpiredListTable,
    LineWarningDetailTable,
)
from transit_odp.data_quality.views.base import JourneyListBaseView
from transit_odp.users.views.mixins import OrgUserViewMixin


class LineExpiredListView(JourneyListBaseView):
    data = ExpiredLines
    model = LineExpiredWarning
    table_class = LineExpiredListTable

    def get_queryset(self):
        return super().get_queryset().add_line().add_message()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": self.data.title, "definition": self.data.text})
        return context


class LineMissingBlockIDListView(JourneyListBaseView):
    data = MissingBlockNumber
    model = LineMissingBlockIDWarning
    table_class = JourneyLineListTable

    def get_queryset(self):
        return super().get_queryset().add_line().add_message().order_by("line")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": self.data.title, "definition": self.data.text})
        return context


class LineMissingBlockIDDetailView(OrgUserViewMixin, DetailView):
    template_name = "data_quality/line_detail.html"
    pk_url_kwarg = "warning_pk"

    def get_queryset(self):
        report_id = self.kwargs.get("report_id")
        return LineMissingBlockIDWarning.objects.filter(report_id=report_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        timing_pattern = self.object.vehicle_journeys.first().timing_pattern
        journeys = (
            self.object.vehicle_journeys.all()
            .add_first_date()
            .add_line_name()
            .add_first_stop()
        )

        table = LineWarningDetailTable(journeys)
        table.paginate(page=self.request.GET.get("page", 1), per_page=10)

        api_url = reverse("dq-api:api-root", host=config.hosts.PUBLISH_HOST)
        back_url = reverse(
            MissingBlockNumber.list_url_name,
            kwargs={
                "pk": self.kwargs.get("pk"),
                "pk1": self.kwargs.get("pk1"),
                "report_id": self.kwargs.get("report_id"),
            },
            host=config.hosts.PUBLISH_HOST,
        )

        context.update(
            {
                "title": MissingBlockNumber.title,
                "subtitle": (
                    f"Line {self.object.service.name} has at least one journey "
                    "which has missing Block Number(s)"
                ),
                "api_root": api_url,
                "back_url": back_url,
                "table": table,
                "report_date": self.object.report.created,
                "service_pattern_id": timing_pattern.service_pattern_id,
                "service_link_id": "",
                "stop_ids": "",
                "affected_stop_ids": "",
            }
        )
        return context
