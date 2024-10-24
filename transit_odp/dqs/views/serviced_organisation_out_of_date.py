from transit_odp.dqs.constants import Checks, ServicedOrganisationOutOfDateObservation
from transit_odp.dqs.tables.serviced_organisation_out_of_date import (
    ServicedOrganisationOutOfDateCodeTable,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView, DQSWarningDetailBaseView


class ServicedOrganisationOutOfDateListView(DQSWarningListBaseView):
    data = ServicedOrganisationOutOfDateObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = Checks.ServicedOrganisationOutOfDate
    dqs_details = "There is at least one serviced organisation that is out of date"

    def get_queryset(self):

        return super().get_queryset()

    def get_table_kwargs(self):
        return {}


class ServicedOrganisationOutOfDateDetailView(DQSWarningDetailBaseView):
    data = ServicedOrganisationOutOfDateObservation
    paginate_by = 10

    def get_context_data(self, **kwargs):

        self._table_name = ServicedOrganisationOutOfDateCodeTable
        self.check = Checks.ServicedOrganisationOutOfDate
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": f"Service {line} has at least one journey linked to a serviced organisation that is out of date",
                "subtitle_description": "Which serviced organisations have been affected?",
                "total_journey_description": "Total serviced organisations",
                "list_text": "serviced organisations",
            }
        )

        return context
