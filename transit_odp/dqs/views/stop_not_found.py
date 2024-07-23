from transit_odp.data_quality.constants import StopNotInNaptanObservation
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.tables.stop_not_found import StopNotFoundInNaptanOnlyTable
from transit_odp.organisation.models import Dataset


class DQSStopMissingNaptanDetailView(DQSWarningDetailBaseView):
    data = StopNotInNaptanObservation
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable
    paginate_by = 10

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        title = self.data.title
        service_code = self.request.GET.get("service")
        line = self.request.GET.get("line")
        page = self.request.GET.get("page", 1)
        qs = self.get_queryset()

        context["title"] = title
        context["subtitle"] = (
            f"Service {service_code} has at least one journey with a stop that "
            "is not found in NaPTAN"
        )
        context["num_of_journeys"] = len(qs)

        context["table"] = StopNotFoundInNaptanOnlyTable(qs, page)
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        dataset_id = self.kwargs.get("pk")
        org_id = self.kwargs.get("pk1")

        qs = Dataset.objects.filter(id=dataset_id, organisation_id=org_id).get_active()
        if not len(qs):
            return qs
        revision_id = qs[0].live_revision_id
        self.check = Checks.StopNotFoundInNaptan

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id
        )

        return qs
