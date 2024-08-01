from transit_odp.data_quality.constants import StopNotInNaptanObservation

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.models.warnings import StopMissingNaptanWarning

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.tables import (
    StopMissingNaptanListTable,
    StopMissingNaptanWarningTimingTable,
    StopMissingNaptanWarningVehicleTable,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)
from transit_odp.dqs.constants import (
    Checks,
    StopNotInNaptanObservation as DQSStopNotInNaptanObservation,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView
from waffle import flag_is_active


class StopMissingNaptanListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = StopNotInNaptanObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None
        self.model = StopMissingNaptanWarning
        self.table_class = StopMissingNaptanListTable

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.StopNotFoundInNaptan
    dqs_details = "There is at least one stop that is not registered with NaPTAN"

    def get_queryset(self):
        if not self.is_dqs_new_report:
            # The synthetic stop can appear in multiple service patterns, here we just pick
            # an arbitrary service pattern to help the user.
            return (
                super()
                .get_queryset()
                .exclude_null_service_patterns()
                .add_message()
                .add_line()
            )

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_dqs_new_report:
            self.data = DQSStopNotInNaptanObservation

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


class StopMissingNaptanDetailView(TwoTableDetailView):
    data = StopNotInNaptanObservation
    model = StopMissingNaptanWarning
    tables = [StopMissingNaptanWarningTimingTable, StopMissingNaptanWarningVehicleTable]

    def get_table1_kwargs(self):
        kwargs = super().get_table1_kwargs()
        stop = self.warning.stop
        kwargs[
            "warning_message"
        ] = f"Synthetic stop(s) ({stop.atco_code}) not found in NaPTAN."
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_name = self.warning.get_service_pattern().service.name

        context["title"] = self.data.title
        context["subtitle"] = (
            f"Line {service_name} has at least one journey where stop(s) are not in "
            f"NaPTAN"
        )
        return context
