from transit_odp.dqs.constants import (
    Checks,
    FirstStopNotTimingPointObservation,
    LastStopNotTimingPointObservation,
)
from transit_odp.dqs.views.base import DQSWarningDetailBaseView, DQSWarningListBaseView
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


class LastStopNotTimingListView(DQSWarningListBaseView):
    data = LastStopNotTimingPointObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.LastStopIsNotATimingPoint
    dqs_details = (
        "There is at least one journey where the last stop is not a timing point"
    )

    def get_queryset(self):

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):

        self.data = LastStopNotTimingPointObservation
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

        kwargs = {}
        if not self.is_dqs_new_report:
            kwargs = super().get_table_kwargs()
        return kwargs


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
