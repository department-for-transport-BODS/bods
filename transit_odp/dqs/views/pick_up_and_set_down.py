from transit_odp.dqs.constants import Checks, LastStopPickUpOnlyObservation
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.pick_up_and_set_down import LastStopIsSetDownOnlyTable


class LastStopPickUpDetailView(DQSWarningDetailBaseView):
    data = LastStopPickUpOnlyObservation

    def get_context_data(self, **kwargs):

        self._table_name = LastStopIsSetDownOnlyTable
        self.check = Checks.LastStopIsPickUpOnly
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": (
                    f"Service {line} has at least one journey where the last stop is "
                    f"designated as pick up only"
                )
            }
        )
        return context
