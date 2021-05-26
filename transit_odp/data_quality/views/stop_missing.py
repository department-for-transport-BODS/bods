from transit_odp.data_quality.constants import NoTimingPointFor15MinutesObservation
from transit_odp.data_quality.models.warnings import TimingMissingPointWarning
from transit_odp.data_quality.tables import (
    MissingStopWarningDetailTable,
    MissingStopWarningVehicleTable,
)
from transit_odp.data_quality.tables.base import TimingPatternListTable
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class MissingStopListView(TimingPatternsListBaseView):
    data = NoTimingPointFor15MinutesObservation
    model = TimingMissingPointWarning
    table_class = TimingPatternListTable

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("timing_pattern__service_pattern__service")
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
                    "Following timing pattern(s) have been observed to "
                    "have timing point(s) missing."
                ),
                "observation": self.data,
            }
        )
        return context


class MissingStopDetailView(TwoTableDetailView):
    data = NoTimingPointFor15MinutesObservation
    model = TimingMissingPointWarning
    tables = [MissingStopWarningDetailTable, MissingStopWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = f"Line {line_name} has {title.lower()}"
        return context
