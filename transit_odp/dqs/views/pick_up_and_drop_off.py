from transit_odp.dqs.constants import (
    Checks,
    FirstStopSetDownOnlyObservation,
    LastStopPickUpOnlyObservation,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView


class LastStopPickUpListView(DQSWarningListBaseView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    check = Checks.LastStopIsPickUpOnly
    dqs_details = "There is at least one journey where the last stop is designated as pick up only"

    def get_queryset(self):

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):

        self.data = LastStopPickUpOnlyObservation
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


class FirstStopDropOffListView(DQSWarningListBaseView):

    check = Checks.FirstStopIsSetDown
    dqs_details = "There is at least one journey where the first stop is designated as set down only"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_queryset(self):

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):

        self.data = FirstStopSetDownOnlyObservation
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
