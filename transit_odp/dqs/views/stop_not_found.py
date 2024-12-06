from transit_odp.dqs.constants import Checks, StopNotInNaptanObservation
from transit_odp.dqs.views.base import DQSWarningDetailBaseView, DQSWarningListBaseView
from transit_odp.dqs.tables.stop_not_found import StopNotFoundInNaptanOnlyTable


class StopNotFoundInNaptanListView(DQSWarningListBaseView):
    data = StopNotInNaptanObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.StopNotFoundInNaptan
    dqs_details = "There is at least one stop that is not registered with NaPTAN"

    def get_queryset(self):

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):

        self.data = StopNotInNaptanObservation
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": self.data.preamble,
                "resolve": self.data.resolve,
            }
        )
        return context

    def get_table_kwargs(self):

        return {}


class StopNotFoundInNaptanDetailView(DQSWarningDetailBaseView):
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
