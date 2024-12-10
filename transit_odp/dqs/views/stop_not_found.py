from transit_odp.dqs.constants import Checks, StopNotInNaptanObservation
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.stop_not_found import StopNotFoundInNaptanOnlyTable


class StopMissingNaptanDetailView(DQSWarningDetailBaseView):
    data = StopNotInNaptanObservation

    def get_context_data(self, **kwargs):

        self.check = Checks.StopNotFoundInNaptan
        self._table_name = StopNotFoundInNaptanOnlyTable
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": (
                    f"Service {line} has at least one journey with a stop that "
                    "is not found in NaPTAN"
                )
            }
        )
        return context
