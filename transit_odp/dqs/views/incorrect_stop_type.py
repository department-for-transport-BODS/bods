from transit_odp.data_quality.constants import IncorrectStopTypeObservation

from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningDetailBaseView
from transit_odp.dqs.tables.base import DQSWarningDetailsBaseTable
from transit_odp.dqs.tables.incorrect_stop_type import IncorrectStopTypeTable
from transit_odp.dqs.models import Report


class DQSIncorrectStopTypeDetailView(DQSWarningDetailBaseView):
    data = IncorrectStopTypeObservation
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable
    paginate_by = 10

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        title = self.data.title
        service_code = self.request.GET.get("service")
        page = self.request.GET.get("page", 1)
        qs = self.get_queryset()

        context["title"] = title
        context["subtitle"] = (
            f"Service {service_code} has at least one journey with a stop "
            "of the incorrect type in NaPTAN."
        )
        context["num_of_journeys"] = len(qs)
        context["table"] = IncorrectStopTypeTable(qs, page)
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")

        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        self.check = Checks.IncorrectStopType

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id, True
        )

        return qs
