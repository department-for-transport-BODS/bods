from transit_odp.dqs.constants import Checks, NoTimingPointMoreThan15MinsObservation
from transit_odp.dqs.tables.no_timing_point_more_than_15_mins import (
    NoTimingPointMoreThan15MinsCodeTable,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView, DQSWarningDetailBaseView
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.models import Report


class NoTimingPointMoreThan15MinsListView(DQSWarningListBaseView):
    data = NoTimingPointMoreThan15MinsObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.NoTimingPointMoreThan15Mins
    dqs_details = "There is at least one journey with a pair of timing points of more than 15 minutes"

    def get_queryset(self):

        return super().get_queryset()

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": self.data.preamble,
                "resolve": self.data.resolve,
                "impacts": self.data.impacts,
            }
        )
        return context

    def get_table_kwargs(self):
        return {}


class NoTimingPointMoreThan15MinsDetailView(DQSWarningDetailBaseView):
    data = NoTimingPointMoreThan15MinsObservation
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
            f"Service {line} has at least one journey with a duplicate journey code"
        )
        context["num_of_journeys"] = len(qs)

        context["table"] = NoTimingPointMoreThan15MinsCodeTable(qs, page)
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        service = self.request.GET.get("service")
        line = self.request.GET.get("line")
        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        self.check = Checks.NoTimingPointMoreThan15Mins

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id, service, line
        )

        return qs
