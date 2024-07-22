from transit_odp.data_quality.constants import (
    FirstStopNotTimingPointObservation,
    LastStopNotTimingPointObservation,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.models.warnings import (
    TimingFirstWarning,
    TimingLastWarning,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.tables import (
    TimingFirstWarningDetailTable,
    TimingFirstWarningVehicleTable,
    TimingLastWarningDetailTable,
    TimingLastWarningVehicleTable,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.tables.base import (
    TimingPatternListTable,
    DQSWarningListBaseTable,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningListBaseView
from waffle import flag_is_active


class LastStopNotTimingListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = LastStopNotTimingPointObservation
    
    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")
    
    check = Checks.LastStopIsNotATimingPoint
    dqs_details = (
        "There is at least one journey where the last stop is not a timing point"
    )

    if not is_new_data_quality_service_active:
        model = TimingLastWarning
        table_class = TimingPatternListTable
    else:
        model = ObservationResults
        table_class = DQSWarningListBaseTable

    def get_queryset(self):
        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_message().add_line()

        return DQSWarningListBaseView.get_queryset(self)

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


class FirstStopNotTimingListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = FirstStopNotTimingPointObservation
    
    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")
    
    check = Checks.FirstStopIsNotATimingPoint
    dqs_details = (
        "There is at least one journey where the first stop is not a timing point"
    )

    if not is_new_data_quality_service_active:
        model = TimingFirstWarning
        table_class = TimingPatternListTable
    else:
        model = ObservationResults
        table_class = DQSWarningListBaseTable

    def get_queryset(self):

        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_message().add_line()

        return DQSWarningListBaseView.get_queryset(self)

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
