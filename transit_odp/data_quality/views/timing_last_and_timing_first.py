from transit_odp.data_quality.constants import (
    FirstStopNotTimingPointObservation,
    LastStopNotTimingPointObservation,
)
from transit_odp.data_quality.models.warnings import (
    TimingFirstWarning,
    TimingLastWarning,
)
from transit_odp.data_quality.tables import (
    TimingFirstWarningDetailTable,
    TimingFirstWarningVehicleTable,
    TimingLastWarningDetailTable,
    TimingLastWarningVehicleTable,
)
from transit_odp.data_quality.tables.base import TimingPatternListTable
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class LastStopNotTimingListView(TimingPatternsListBaseView):
    data = LastStopNotTimingPointObservation
    model = TimingLastWarning
    table_class = TimingPatternListTable

    def get_queryset(self):
        return super().get_queryset().add_message().add_line()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Last stop in the following timing pattern(s) have been observed "
                    "to not have timing points."
                ),
            }
        )
        return context


class LastStopNotTimingDetailView(TwoTableDetailView):
    data = LastStopNotTimingPointObservation
    model = TimingLastWarning
    tables = [TimingLastWarningDetailTable, TimingLastWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = self.data.title
        context[
            "subtitle"
        ] = f"Line {line_name} has at least one journey where the {title.lower()}"
        return context


class FirstStopNotTimingListView(TimingPatternsListBaseView):
    data = FirstStopNotTimingPointObservation
    model = TimingFirstWarning
    table_class = TimingPatternListTable

    def get_queryset(self):
        return super().get_queryset().add_message().add_line()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "First stop in the following timing pattern(s) have been observed "
                    "to not have timing points."
                ),
            }
        )
        return context


class FirstStopNotTimingDetailView(TwoTableDetailView):
    data = FirstStopNotTimingPointObservation
    model = TimingFirstWarning
    tables = [TimingFirstWarningDetailTable, TimingFirstWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context[
            "subtitle"
        ] = f"Line {line_name} has at least one journey where the {title.lower()}"
        return context
