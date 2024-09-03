from transit_odp.dqs.constants import Checks, NoTimingPointMoreThan15MinsObservation
from transit_odp.dqs.tables.no_timing_point_more_than_15_mins import (
    NoTimingPointMoreThan15MinsCodeTable,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView, DQSWarningDetailBaseView


class NoTimingPointMoreThan15MinsListView(DQSWarningListBaseView):
    data = NoTimingPointMoreThan15MinsObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.NoTimingPointMoreThan15Minutes
    dqs_details = "There is at least one journey with a pair of timing points of more than 15 minutes"

    def get_queryset(self):
        return super().get_queryset()

    def get_table_kwargs(self):
        return {}


class NoTimingPointMoreThan15MinsDetailView(DQSWarningDetailBaseView):
    data = NoTimingPointMoreThan15MinsObservation

    def get_context_data(self, **kwargs):

        self._table_name = NoTimingPointMoreThan15MinsCodeTable
        self.check = Checks.NoTimingPointMoreThan15Minutes
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": f"Service {line} has at least one journey with a pair of timings of more than 15 minutes"
            }
        )
        return context
