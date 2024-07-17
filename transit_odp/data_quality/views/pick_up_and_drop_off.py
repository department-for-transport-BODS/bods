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
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable
# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.views.base import (
    DetailBaseView,
    TimingPatternsListBaseView,
    TwoTableDetailView,
)
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views import DQSWarningListBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable

from waffle import flag_is_active


class LastStopPickUpListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = LastStopPickUpOnlyObservation
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )
    check = Checks.LastStopIsPickUpOnly
    dqs_details = "There is at least one journey where the last stop is designated as pick up only"

    if not is_new_data_quality_service_active:
        model = TimingDropOffWarning
        table_class = PickUpDropOffListTable
    else:
        model = ObservationResults
        table_class = DQSWarningListBaseTable

    def get_queryset(self):

        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_message().add_line()

        # Calling the qs method of DQSWarningListBaseView
        return DQSWarningListBaseView.get_queryset(self)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following service(s) have been observed to have last "
                    "stop as pick up only."
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


class DQSLastStopPickUpDetailView(DetailBaseView):
    data = LastStopPickUpOnlyObservation
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable
    paginate_by = 10

    def get_context_data(self, **kwargs):
        print("context called")
        context = super().get_context_data(**kwargs)

        title = self.data.title
        service_code = self.request.GET.get("service")
        line = self.request.GET.get("line")
        # line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = (
            f"Service {service_code} has at least one journey where the last stop is "
            f"designated as pick up only"
        )

        print("df imported")
        qs = self.get_queryset()
        page = self.request.GET.get("page", 1)
        context["df"] = DQSWarningDetailsBaseTable(qs, page)
        return context

    def get_queryset(self):

        print("Queryset called")

        # DQSWarningListBaseView.get_queryset(self)
        report_id = self.kwargs.get("report_id")
        dataset_id = self.kwargs.get("pk")
        org_id = self.kwargs.get("pk1")

        # qs = Dataset.objects.filter(id=dataset_id, organisation_id=org_id).get_active()
        # if not len(qs):
        #    return qs
        # revision_id = qs[0].live_revision_id
        revision_id = 73
        self.check = Checks.LastStopIsPickUpOnly

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id
        )

        return qs

        # Create data for the dataframe
        data = {
            "start time": ["09:00", "12:30", "15:45"],
            "direction": ["North", "South", "West"],
            "last stop": ["Station A", "Station B", "Station C"],
        }

        # Create the dataframe
        df = pd.DataFrame(data)
        return df


class FirstStopDropOffListView(TimingPatternsListBaseView, DQSWarningListBaseView):
    data = FirstStopSetDownOnlyObservation
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )
    check = Checks.FirstStopIsSetDown
    dqs_details = "There is at least one journey where the first stop is designated as set down only"
    if not is_new_data_quality_service_active:
        model = TimingPickUpWarning
        table_class = PickUpDropOffListTable
    else:
        model = ObservationResults
        table_class = DQSWarningListBaseTable

    def get_queryset(self):

        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_line().add_message()

        # Calling the qs method of DQSWarningListBaseView
        return DQSWarningListBaseView.get_queryset(self)

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
