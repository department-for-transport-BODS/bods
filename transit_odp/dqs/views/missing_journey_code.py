from transit_odp.dqs.constants import Checks, MissingJourneyCodeObservation
from transit_odp.dqs.tables.missing_journey_code import MissingJourneyCodeTable
from transit_odp.dqs.views.base import DQSWarningListBaseView, DQSWarningDetailBaseView


class MissingJourneyCodeListView(DQSWarningListBaseView):
    data = MissingJourneyCodeObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.MissingJourneyCode
    dqs_details = "There is at least one journey that is missing a journey code "

    def get_queryset(self):

        return super().get_queryset()

    def get_table_kwargs(self):
        return {}


class MissingJourneyCodeDetailView(DQSWarningDetailBaseView):
    data = MissingJourneyCodeObservation

    def get_context_data(self, **kwargs):

        self._table_name = MissingJourneyCodeTable
        self.check = Checks.MissingJourneyCode
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": f"Service {line} has at least one journey with a missing journey code"
            }
        )
        return context
