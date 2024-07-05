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
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from waffle import flag_is_active


class LastStopNotTimingListView(TimingPatternsListBaseView):
    data = LastStopNotTimingPointObservation
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )
    model = (
        TimingLastWarning
        if not is_new_data_quality_service_active
        else ObservationResults
    )
    table_class = TimingPatternListTable

    def get_queryset(self):
        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_message().add_line()

        report_id = self.kwargs.get("report_id")
        revision_id = self.kwargs.get("pk")
        check = Checks.LastStopIsNotATimingPoint
        message = (
            "There is at least one journey where the last stop is not a timing point"
        )
        return self.model.objects.get_observations_grouped(
            report_id, check, revision_id, message
        )

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
                "resolve": self.data.resolve,
            }
        )
        return context

    def get_table_kwargs(self):

        kwargs = {}
        if not self.is_new_data_quality_service_active:
            kwargs = super().get_table_kwargs()
        return kwargs


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
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )
    model = (
        TimingFirstWarning
        if not is_new_data_quality_service_active
        else ObservationResults
    )
    table_class = TimingPatternListTable

    def get_queryset(self):
        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_message().add_line()
        else:
            report_id = self.kwargs.get("report_id")
            revision_id = self.kwargs.get("pk")
            check = Checks.LastStopIsNotATimingPoint
            message = "There is at least one journey where the first stop is not a timing point"
            return self.model.objects.get_observations_grouped(
                report_id, check, revision_id, message
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following service(s) have been observed to not have the first stop set "
                    "as a timing point."
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
