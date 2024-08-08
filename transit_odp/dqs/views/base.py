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


class DQSWarningDetailBaseView(MultiTableMixin, TemplateView):
    template_name = "dqs/observation_detail.html"
    model = None
    related_model = None
    related_object = None
    tables = []
    paginate_by = 10

    @property
    def data(self):
        raise NotImplementedError("Warning detail views must have data attribute")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Map variables defined largely as empty strings, with values overridden
        # in views as needed for that map
        revision_id = kwargs.get("pk")
        context.update(
            {
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
