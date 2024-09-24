from transit_odp.dqs.constants import Checks, IncorrectLicenceNumberObservation
from transit_odp.dqs.views.base import DQSWarningListBaseView


class IncorrectLicenceNumberListView(DQSWarningListBaseView):
    data = IncorrectLicenceNumberObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.IncorrectLicenceNumber

    def get_queryset(self):

        self.col_name = "lic"
        self.is_details_link = False
        return super().get_queryset()

    def get_table_kwargs(self):
        return {}
