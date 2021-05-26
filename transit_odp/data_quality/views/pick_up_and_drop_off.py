from transit_odp.data_quality.constants import (
    FirstStopSetDownOnlyObservation,
    LastStopPickUpOnlyObservation,
)
from transit_odp.data_quality.models.warnings import (
    TimingDropOffWarning,
    TimingPickUpWarning,
)
from transit_odp.data_quality.tables import (
    FirstStopDropOffOnlyDetail,
    FirstStopDropOffOnlyVehicleTable,
    LastStopPickUpOnlyDetail,
    LastStopPickUpOnlyVehicleTable,
    PickUpDropOffListTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class LastStopPickUpListView(TimingPatternsListBaseView):
    data = LastStopPickUpOnlyObservation
    model = TimingDropOffWarning
    table_class = PickUpDropOffListTable

    def get_queryset(self):
        return super().get_queryset().add_message().add_line()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following timing pattern(s) have been observed to have last "
                    "stop as pick up only."
                ),
            }
        )
        return context


class LastStopPickUpDetailView(TwoTableDetailView):
    data = LastStopPickUpOnlyObservation
    model = TimingDropOffWarning
    tables = [LastStopPickUpOnlyDetail, LastStopPickUpOnlyVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = (
            f"Line {line_name} has at least one journey where the last stop is "
            f"designated as pick up only"
        )
        return context


class FirstStopDropOffListView(TimingPatternsListBaseView):
    data = FirstStopSetDownOnlyObservation
    model = TimingPickUpWarning
    table_class = PickUpDropOffListTable

    def get_queryset(self):
        return super().get_queryset().add_line().add_message()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following timing pattern(s) have been observed to have first "
                    "stop as set down only."
                ),
            }
        )
        return context


class FirstStopDropOffDetailView(TwoTableDetailView):
    data = FirstStopSetDownOnlyObservation
    model = TimingPickUpWarning
    tables = [FirstStopDropOffOnlyDetail, FirstStopDropOffOnlyVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = (
            f"Line {line_name} has at least one journey where the first stop is "
            f"designated as set down only"
        )
        return context
