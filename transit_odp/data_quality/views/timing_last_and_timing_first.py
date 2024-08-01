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
from transit_odp.data_quality.tables.base import TimingPatternListTable

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)
from transit_odp.dqs.constants import (
    Checks,
    FirstStopNotTimingPointObservation as DQSFirstStopNotTimingPointObservation,
    LastStopNotTimingPointObservation as DQSLastStopNotTimingPointObservation,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView
from waffle import flag_is_active


class LastStopNotTimingListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = LastStopNotTimingPointObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = TimingLastWarning
        self.table_class = TimingPatternListTable

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.LastStopIsNotATimingPoint
    dqs_details = (
        "There is at least one journey where the last stop is not a timing point"
    )

    def get_queryset(self):
        if not self.is_dqs_new_report:
            return super().get_queryset().add_message().add_line()

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.is_dqs_new_report:
            self.data = DQSLastStopNotTimingPointObservation

        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": self.data.preamble,
                "resolve": self.data.resolve,
            }
        )
        return context

    def get_table_kwargs(self):

        kwargs = {}
        if not self.is_dqs_new_report:
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = TimingFirstWarning
        self.table_class = TimingPatternListTable

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.FirstStopIsNotATimingPoint
    dqs_details = (
        "There is at least one journey where the first stop is not a timing point"
    )

    def get_queryset(self):
        if not self.is_dqs_new_report:
            return super().get_queryset().add_message().add_line()

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.is_dqs_new_report:
            self.data = DQSFirstStopNotTimingPointObservation

        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": self.data.preamble,
                "resolve": self.data.resolve,
            }
        )
        return context

    def get_table_kwargs(self):
        kwargs = {}
        if not self.is_dqs_new_report:
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
