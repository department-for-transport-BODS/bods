from transit_odp.dqs.constants import Checks, MissingBusWorkingNumberObservation
from transit_odp.dqs.tables.missing_bus_working_number import (
    MissingBusWorkingNumberCodeTable,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView, DQSWarningDetailBaseView


class MissingBusWorkingNumberListView(DQSWarningListBaseView):
    data = MissingBusWorkingNumberObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.MissingBusWorkingNumber
    dqs_details = "There is at least one journey that is missing a bus working number"

    def get_queryset(self):

        return super().get_queryset()

    def get_table_kwargs(self):
        return {}


class MissingBusWorkingNumberDetailView(DQSWarningDetailBaseView):
    data = MissingBusWorkingNumberObservation
    paginate_by = 10

    def get_context_data(self, **kwargs):

        self._table_name = MissingBusWorkingNumberCodeTable
        self.check = Checks.MissingBusWorkingNumber
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": f"Service {line} has at least one journey with a missing bus working number"
            }
        )

        return context
