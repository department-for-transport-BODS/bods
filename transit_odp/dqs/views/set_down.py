from transit_odp.dqs.constants import Checks, FirstStopSetDownOnlyObservation
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.set_down import FirstStopIsSetDownOnlyTable


class FirstStopSetDownDetailView(DQSWarningDetailBaseView):
    data = FirstStopSetDownOnlyObservation

    def get_context_data(self, **kwargs):

        self._table_name = FirstStopIsSetDownOnlyTable
        self.check = Checks.FirstStopIsSetDown
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": (
                    f"Service {line} has at least one journey where the first stop is "
                    "designated as set down only"
                )
            }
        )
        return context
