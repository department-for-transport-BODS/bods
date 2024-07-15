from django.shortcuts import render
from django_tables2 import SingleTableView

from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable
from transit_odp.organisation.models import Dataset

class DQSWarningListBaseView(SingleTableView):
    template_name = "data_quality/warning_list.html"
    table_class = DQSWarningListBaseTable
    model = ObservationResults
    paginate_by = 10
    check: Checks = Checks.DefaultCheck
    dqs_details: str = None

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        dataset_id = self.kwargs.get("pk")
        org_id = self.kwargs.get("pk1")

        qs = Dataset.objects.filter(id=dataset_id, organisation_id=org_id).get_active()
        if not len(qs):
            return qs
        revision_id = qs[0].live_revision_id

        if self.dqs_details:
            return self.model.objects.get_observations_grouped(
                report_id, self.check, revision_id, self.dqs_details
            )

        return self.model.objects.get_observations(report_id, self.check, revision_id)

    def get_table_kwargs(self):
        pass
