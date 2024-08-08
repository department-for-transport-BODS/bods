from transit_odp.dqs.constants import Checks, DuplicateJourneyCodeObservation
from transit_odp.dqs.tables.duplicate_journey_code import DuplicateJourneyCodeTable
from transit_odp.dqs.views.base import DQSWarningListBaseView, DQSWarningDetailBaseView


class DuplicateJourneyCodeListView(DQSWarningListBaseView):
    data = DuplicateJourneyCodeObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.DuplicateJourneyCode
    dqs_details = "There is at least one journey that has a duplicate journey code "

    def get_queryset(self):

        return super().get_queryset()

    def get_table_kwargs(self):
        return {}


class DuplicateJourneyCodeDetailView(DQSWarningDetailBaseView):

    data = DuplicateJourneyCodeObservation

    def get_context_data(self, **kwargs):

        self._table_name = DuplicateJourneyCodeTable
        self.check = Checks.DuplicateJourneyCode
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": f"Service {line} has at least one journey with a duplicate journey code"
            }
        )
        return context
