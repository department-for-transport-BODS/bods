from django_tables2 import SingleTableView
from transit_odp.dqs.tables import DQSWarningListBaseTable
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks


# Create your views here.


class DQSWarningListBaseView(SingleTableView):
    template_name = "data_quality/warning_list.html"
    table_class = DQSWarningListBaseTable
    model = ObservationResults
    paginate_by = 10
    check: Checks = Checks.DefaultCheck

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        revision_id = self.kwargs.get("pk")
        print(
            f"Calling DQS Warning List base view: {report_id}, {revision_id}, {self.check}"
        )
        return self.model.objects.get_observations(report_id, self.check, revision_id)

    def get_table_kwargs(self):
        pass
