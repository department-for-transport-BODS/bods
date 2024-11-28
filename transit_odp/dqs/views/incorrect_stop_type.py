from transit_odp.dqs.constants import Checks, IncorrectStopTypeObservation
from transit_odp.dqs.views.base import DQSWarningListBaseView, DQSWarningDetailBaseView
from transit_odp.dqs.tables.incorrect_stop_type import IncorrectStopTypeTable


class IncorrectStopTypeListView(DQSWarningListBaseView):
    data = IncorrectStopTypeObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    check = Checks.IncorrectStopType
    dqs_details = "There is at least one stop with an incorrect stop type"

    def get_queryset(self):

        # Calling the qs method of DQSWarningListBaseView
        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):

        self.data = IncorrectStopTypeObservation
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": self.data.preamble,
                "extra_info": self.data.extra_info,
                "resolve": self.data.resolve,
            }
        )
        return context

    def get_table_kwargs(self):

        return {}


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
