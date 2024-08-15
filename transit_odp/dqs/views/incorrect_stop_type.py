from transit_odp.data_quality.constants import IncorrectStopTypeObservation

from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.tables.incorrect_stop_type import IncorrectStopTypeTable
from transit_odp.dqs.models import Report


class IncorrectStopTypeDetailView(DQSWarningDetailBaseView):
    data = IncorrectStopTypeObservation

    def get_context_data(self, **kwargs):

        self.check = Checks.IncorrectStopType
        self._table_name = IncorrectStopTypeTable
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": (
                    f"Service {line} has at least one journey with a stop"
                    " of the incorrect type in NaPTAN."
                )
            }
        )
        return context
