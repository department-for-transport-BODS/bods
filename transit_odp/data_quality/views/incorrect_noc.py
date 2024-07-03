from transit_odp.data_quality.constants import IncorrectNocObservation
from transit_odp.data_quality.models.warnings import IncorrectNOCWarning
from transit_odp.data_quality.tables.incorrect_noc import IncorrectNOCListTable
from transit_odp.data_quality.views.base import WarningListBaseView
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from waffle import flag_is_active

class IncorrectNOCListView(WarningListBaseView):
    data = IncorrectNocObservation
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )
    model = (
        IncorrectNOCWarning
        if not is_new_data_quality_service_active
        else ObservationResults
    )
    table_class = IncorrectNOCListTable

    def get_queryset(self):

        # For older DQS
        if not self.is_new_data_quality_service_active:
            qs = super().get_queryset()
            return qs.add_message()

        report_id = self.kwargs.get("report_id")
        revision_id = self.kwargs.get("pk")
        check = Checks.IncorrectNoc
        return self.model.objects.get_observations(report_id, check, revision_id)

    def get_table_kwargs(self):

        kwargs = {}
        if not self.is_new_data_quality_service_active:
            kwargs = super().get_table_kwargs()
            kwargs.update(
                {"message_col_verbose_name": "Summary", "count": self.row_count}
            )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "resolve": self.data.resolve,
                "preamble": (
                    "The following service(s) have been observed to have incorrect "
                    "national operator code(s)."
                ),
                "is_new_data_quality_service_active": self.is_new_data_quality_service_active,
            }
        )
        return context
