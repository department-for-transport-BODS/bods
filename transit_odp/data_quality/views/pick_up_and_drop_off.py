from transit_odp.data_quality.constants import (
    FirstStopSetDownOnlyObservation,
    LastStopPickUpOnlyObservation,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.models.warnings import (
    TimingDropOffWarning,
    TimingPickUpWarning,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.tables import (
    FirstStopDropOffOnlyDetail,
    FirstStopDropOffOnlyVehicleTable,
    LastStopPickUpOnlyDetail,
    LastStopPickUpOnlyVehicleTable,
    PickUpDropOffListTable,
)

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.views.base import (
    DetailBaseView,
    TimingPatternsListBaseView,
    TwoTableDetailView,
)
from transit_odp.dqs.constants import (
    Checks,
    FirstStopSetDownOnlyObservation as DQSFirstStopSetDownOnlyObservation,
    LastStopPickUpOnlyObservation as DQSLastStopPickUpOnlyObservation,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView
from waffle import flag_is_active


class LastStopPickUpListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = LastStopPickUpOnlyObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_new_data_quality_service_active:
            self.model = TimingDropOffWarning
            self.table_class = PickUpDropOffListTable

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.LastStopIsPickUpOnly
    dqs_details = "There is at least one journey where the last stop is designated as pick up only"

    def get_queryset(self):

        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_message().add_line()

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):
        if self.is_dqs_new_report:
            self.data = DQSLastStopPickUpOnlyObservation
        context = super().get_context_data(**kwargs)

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
        if not self.is_new_data_quality_service_active:
            kwargs = super().get_table_kwargs()
        return kwargs


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


class FirstStopDropOffListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = FirstStopSetDownOnlyObservation
    check = Checks.FirstStopIsSetDown
    dqs_details = "There is at least one journey where the first stop is designated as set down only"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = TimingPickUpWarning
        self.table_class = PickUpDropOffListTable

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    def get_queryset(self):
        if not self.is_dqs_new_report:
            return super().get_queryset().add_message().add_line()

        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):
        if self.is_dqs_new_report:
            self.data = DQSFirstStopSetDownOnlyObservation
        context = super().get_context_data(**kwargs)

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
        if not self.is_new_data_quality_service_active:
            kwargs = super().get_table_kwargs()
        return kwargs


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
