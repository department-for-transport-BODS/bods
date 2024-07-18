from transit_odp.data_quality.constants import (
    FirstStopSetDownOnlyObservation,
    LastStopPickUpOnlyObservation,
)

from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.tables.pick_up_and_set_down import LastStopIsSetDownOnlyTable
from transit_odp.organisation.models import Dataset


class DQSLastStopPickUpDetailView(DQSWarningDetailBaseView):
    data = LastStopPickUpOnlyObservation
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable
    paginate_by = 10

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        title = self.data.title
        service_code = self.request.GET.get("service")
        line = self.request.GET.get("line")

        qs = self.get_queryset()

        context["title"] = title
        context["subtitle"] = (
            f"Service {service_code} has at least one journey where the last stop is "
            f"designated as pick up only"
        )
        context["num_of_journeys"] = len(qs)

        page = self.request.GET.get("page", 1)
        context["table"] = LastStopIsSetDownOnlyTable(qs, page)
        return context

    def get_queryset(self):

        # DQSWarningListBaseView.get_queryset(self)
        report_id = self.kwargs.get("report_id")
        dataset_id = self.kwargs.get("pk")
        org_id = self.kwargs.get("pk1")

        qs = Dataset.objects.filter(id=dataset_id, organisation_id=org_id).get_active()
        if not len(qs):
            return qs
        revision_id = qs[0].live_revision_id
        self.check = Checks.LastStopIsPickUpOnly

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id
        )

        return qs
