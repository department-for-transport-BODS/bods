from transit_odp.data_quality.constants import SlowTimingPointObservation
from transit_odp.data_quality.models.warnings import SlowTimingWarning
from transit_odp.data_quality.tables import (
    SlowTimingWarningTimingTable,
    SlowTimingWarningVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class SlowTimingsDetailView(TwoTableDetailView):
    data = SlowTimingPointObservation
    model = SlowTimingWarning
    tables = [SlowTimingWarningTimingTable, SlowTimingWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = f"Line {line_name} has {title.lower()}"
        return context


class SlowTimingsListView(TimingPatternsListBaseView):
    data = SlowTimingPointObservation
    model = SlowTimingWarning

    def get_queryset(self):
        return super().get_queryset().add_message().add_line()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Following timing pattern(s) have been observed to have slow "
                    "timing links."
                ),
            }
        )
        return context
