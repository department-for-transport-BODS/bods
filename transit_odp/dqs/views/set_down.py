from transit_odp.data_quality.constants import FirstStopSetDownOnlyObservation
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.tables.set_down import FirstStopIsSetDownOnlyTable
from transit_odp.dqs.models import Report


class DQSFirstStopSetDownDetailView(DQSWarningDetailBaseView):
    data = FirstStopSetDownOnlyObservation
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
            f"Service {service_code} has at least one journey where the first stop is "
            "designated as set down only"
        )
        context["num_of_journeys"] = len(qs)

        context["table"] = FirstStopIsSetDownOnlyTable(qs, page)
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")

        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        self.check = Checks.FirstStopIsSetDown

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id
        )

        return qs
