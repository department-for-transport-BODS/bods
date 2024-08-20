from transit_odp.dqs.constants import Checks, CancelledServiceAppearingActiveObservation
from transit_odp.dqs.views.base import DQSWarningListBaseView


class CancelledServiceAppearingActiveListView(DQSWarningListBaseView):
    data = CancelledServiceAppearingActiveObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.CancelledServiceAppearingActive

    def get_queryset(self):

        self.col_name = "cancelled_service"
        self.is_details_link = False
        return super().get_queryset()

    def get_table_kwargs(self):
        return {}
