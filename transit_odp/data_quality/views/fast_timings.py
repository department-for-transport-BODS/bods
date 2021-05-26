from transit_odp.data_quality.constants import FastTimingPointObservation
from transit_odp.data_quality.models.warnings import FastTimingWarning
from transit_odp.data_quality.tables.fast_timings import (
    FastTimingWarningTimingTable,
    FastTimingWarningVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class FastTimingDetailView(TwoTableDetailView):
    data = FastTimingPointObservation
    model = FastTimingWarning
    tables = [FastTimingWarningTimingTable, FastTimingWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = f"Line {line_name} has {title.lower()}"
        return context


class FastTimingListView(TimingPatternsListBaseView):
    data = FastTimingPointObservation
    model = FastTimingWarning

    def get_queryset(self):
        return super().get_queryset().add_line().add_message()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Following timing pattern(s) have been observed to have "
                    "fast timing links."
                ),
            }
        )
        return context
