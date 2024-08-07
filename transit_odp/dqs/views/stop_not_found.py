from transit_odp.data_quality.constants import StopNotInNaptanObservation
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.tables.stop_not_found import StopNotFoundInNaptanOnlyTable
from transit_odp.dqs.models import Report


class DQSStopMissingNaptanDetailView(DQSWarningDetailBaseView):
    data = StopNotInNaptanObservation
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
            f"Service {line} has at least one journey with a stop that "
            "is not found in NaPTAN"
        )
        context["num_of_journeys"] = len(qs)

        context["table"] = StopNotFoundInNaptanOnlyTable(qs, page)
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        service = self.request.GET.get("service")
        line = self.request.GET.get("line")

        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        print(f"revision_id is {revision_id}")
        self.check = Checks.StopNotFoundInNaptan

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id, service, line
        )

        return qs
