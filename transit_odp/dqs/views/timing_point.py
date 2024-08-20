from transit_odp.dqs.constants import (
    Checks,
    FirstStopNotTimingPointObservation,
    LastStopNotTimingPointObservation,
)
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.timing_point import (
    FirstStopIsTimingPointOnlyTable,
    LastStopIsTimingPointOnlyTable,
)


class FirstStopNotTimingPointDetailView(DQSWarningDetailBaseView):
    data = FirstStopNotTimingPointObservation

    def get_context_data(self, **kwargs):

        self._table_name = FirstStopIsTimingPointOnlyTable
        self.check = Checks.FirstStopIsNotATimingPoint
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": (
                    f"Service {line} has at least one journey where the first stop is "
                    "not a timing point"
                )
            }
        )
        return context


class LastStopNotTimingPointDetailView(DQSWarningDetailBaseView):
    data = LastStopNotTimingPointObservation

    def get_context_data(self, **kwargs):

        self.check = Checks.LastStopIsNotATimingPoint
        self._table_name = LastStopIsTimingPointOnlyTable
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": (
                    f"Service {line} has at least one journey where the last stop is "
                    "not a timing point"
                )
            }
        )
        return context
