from transit_odp.data_quality.constants import StopNotInNaptanObservation
from transit_odp.data_quality.models.warnings import StopMissingNaptanWarning
from transit_odp.data_quality.tables import (
    StopMissingNaptanListTable,
    StopMissingNaptanWarningTimingTable,
    StopMissingNaptanWarningVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class StopMissingNaptanListView(TimingPatternsListBaseView):
    data = StopNotInNaptanObservation
    model = StopMissingNaptanWarning
    table_class = StopMissingNaptanListTable

    def get_queryset(self):
        # The synthetic stop can appear in multiple service patterns, here we just pick
        # an arbitrary service pattern to help the user.
        return (
            super()
            .get_queryset()
            .exclude_null_service_patterns()
            .add_message()
            .add_line()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following timing pattern(s) have been observed to have stops "
                    "that are not in NaPTAN."
                ),
            }
        )
        return context


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
