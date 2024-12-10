from transit_odp.data_quality import constants
from transit_odp.data_quality.tables import (
    BackwardTimingsListTable,
    BackwardTimingsWarningTable,
    BackwardTimingVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class BackwardTimingListView(TimingPatternsListBaseView):
    data = constants.BackwardsTimingObservation
    model = data.model
    table_class = BackwardTimingsListTable

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Following timing pattern(s) have been observed to have backwards "
                    "timing."
                ),
            }
        )
        return context


class BackwardTimingDetailView(TwoTableDetailView):
    data = constants.BackwardsTimingObservation
    model = data.model
    tables = [BackwardTimingsWarningTable, BackwardTimingVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = f"Line {line_name} has {title.lower()}"
        return context
