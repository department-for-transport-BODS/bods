from transit_odp.data_quality.constants import (
    FirstStopNotTimingPointObservation,
    LastStopNotTimingPointObservation,
)
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.tables.timing_point import (
    FirstStopIsTimingPointOnlyTable,
    LastStopIsTimingPointOnlyTable,
)
from transit_odp.dqs.models import Report


class DQSFirstStopNotTimingPointDetailView(DQSWarningDetailBaseView):
    data = FirstStopNotTimingPointObservation
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable
    paginate_by = 10

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        title = self.data.title
        line = self.request.GET.get("line")
        page = self.request.GET.get("page", 1)
        qs = self.get_queryset()

        context["title"] = title
        context["subtitle"] = (
            f"Service {line} has at least one journey where the first stop is "
            "not a timing point"
        )
        context["num_of_journeys"] = len(qs)

        context["table"] = FirstStopIsTimingPointOnlyTable(qs, page)
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        service = self.request.GET.get("service")
        line = self.request.GET.get("line")
        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        self.check = Checks.FirstStopIsNotATimingPoint

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id, service, line
        )

        return qs


class DQSLastStopNotTimingPointDetailView(DQSWarningDetailBaseView):
    data = LastStopNotTimingPointObservation
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable
    paginate_by = 10

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        title = self.data.title
        line = self.request.GET.get("line")
        page = self.request.GET.get("page", 1)
        qs = self.get_queryset()

        context["title"] = title
        context["subtitle"] = (
            f"Service {line} has at least one journey where the last stop is "
            "not a timing point"
        )
        context["num_of_journeys"] = len(qs)

        context["table"] = LastStopIsTimingPointOnlyTable(qs, page)
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        service = self.request.GET.get("service")
        line = self.request.GET.get("line")

        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        self.check = Checks.LastStopIsNotATimingPoint

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id, service, line
        )

        return qs
