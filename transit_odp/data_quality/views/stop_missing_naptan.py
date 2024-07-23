from transit_odp.data_quality.constants import StopNotInNaptanObservation

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.models.warnings import StopMissingNaptanWarning

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.tables import (
    StopMissingNaptanListTable,
    StopMissingNaptanWarningTimingTable,
    StopMissingNaptanWarningVehicleTable,
)
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningListBaseView
from waffle import flag_is_active


class StopMissingNaptanListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = StopNotInNaptanObservation

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.StopNotFoundInNaptan
    dqs_details = "There is at least one stop that is not registered with NaPTAN"

    if not is_new_data_quality_service_active:
        model = StopMissingNaptanWarning
        table_class = StopMissingNaptanListTable
    else:
        model = ObservationResults
        table_class = DQSWarningListBaseTable

    def get_queryset(self):

        if not self.is_new_data_quality_service_active:
            # The synthetic stop can appear in multiple service patterns, here we just pick
            # an arbitrary service pattern to help the user.
            return (
                super()
                .get_queryset()
                .exclude_null_service_patterns()
                .add_message()
                .add_line()
            )

        # Calling the qs method of DQSWarningListBaseView
        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following service(s) have been observed to have a stop that "
                    "is not registered with NaPTAN."
                ),
                "resolve": self.data.resolve,
            }
        )
        return context

    def get_table_kwargs(self):

        kwargs = {}
        if not self.is_new_data_quality_service_active:
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
