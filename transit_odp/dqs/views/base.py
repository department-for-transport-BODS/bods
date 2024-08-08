from typing import Any
from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import MultiTableMixin, SingleTableView
from django_hosts import reverse
import config.hosts

from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable
from transit_odp.dqs.models import Report
from transit_odp.organisation.models import DatasetRevision
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable

class DQSWarningListBaseView(SingleTableView):
    template_name = "data_quality/warning_list.html"
    table_class = DQSWarningListBaseTable
    model = ObservationResults
    paginate_by = 10
    check: Checks = Checks.DefaultCheck
    dqs_details: str = None
    _is_dqs_new_report = None

    @property
    def is_dqs_new_report(self):
        if self._is_dqs_new_report is None:
            report_id = self.kwargs.get("report_id")
            qs = Report.objects.filter(id=report_id)
            self._is_dqs_new_report = True
            if not len(qs):
                self._is_dqs_new_report = False
        return self._is_dqs_new_report

    def get_queryset(self):
        self.model = ObservationResults
        self.table_class = DQSWarningListBaseTable

        report_id = self.kwargs.get("report_id")

        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        qs_revision = (
            DatasetRevision.objects.filter(id=revision_id).get_published().first()
        )
        is_published = False
        if qs_revision:
            is_published = qs_revision.is_published

        if self.dqs_details:
            return self.model.objects.get_observations_grouped(
                report_id, self.check, revision_id, self.dqs_details, is_published
            )

        return self.model.objects.get_observations(
            report_id, self.check, revision_id, self.col_name
        ).distinct()

    def get_table_kwargs(self):
        pass

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": self.data.preamble,
                "resolve": self.data.resolve,
                "impacts": self.data.impacts,
            }
        )
        return context


class DQSWarningDetailBaseView(MultiTableMixin, TemplateView):
    template_name = "dqs/observation_detail.html"
    model = None
    related_model = None
    related_object = None
    tables = []
    paginate_by = 10
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable

    @property
    def data(self):
        raise NotImplementedError("Warning detail views must have data attribute")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Map variables defined largely as empty strings, with values overridden
        # in views as needed for that map
        revision_id = kwargs.get("pk")

        title = self.data.title
        page = self.request.GET.get("page", 1)
        qs = self.get_queryset()

        context.update(
            {
                "title": title,
                "num_of_journeys": len(qs),
                "table": self._table_name(qs, page),
                # for map -- empty strings passed if specific geometry not needed
                "service_pattern_id": "",
                "stop_ids": "",
                "effected_stop_ids": "",
                "service_link_ids": "",
                "api_root": reverse(
                    "dq-api:api-root",
                    host=config.hosts.PUBLISH_HOST,
                ),
                # for backlink -- inheriting views need data attribute set to
                # relevant constant
                "back_url": reverse(
                    self.data.list_url_name,
                    kwargs={
                        "pk": revision_id,
                        "pk1": kwargs.get("pk1"),
                        "report_id": kwargs.get("report_id"),
                    },
                    host=config.hosts.PUBLISH_HOST,
                ),
            }
        )
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        service = self.request.GET.get("service")
        line = self.request.GET.get("line")
        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id, service, line
        )

        return qs
