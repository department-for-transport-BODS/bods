from transit_odp.data_quality.constants import IncorrectNocObservation

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.models.warnings import IncorrectNOCWarning

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.tables.incorrect_noc import IncorrectNOCListTable
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable

# TODO: DQSMIGRATION: FLAGBASED: Remove after flag is enabled (by default)
from transit_odp.data_quality.views.base import WarningListBaseView
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from transit_odp.dqs.views.base import DQSWarningListBaseView
from waffle import flag_is_active


class IncorrectNOCListView(WarningListBaseView, DQSWarningListBaseView):
    data = IncorrectNocObservation

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.IncorrectNoc

    if not is_new_data_quality_service_active:
        model = IncorrectNOCWarning
        table_class = IncorrectNOCListTable
    else:
        model = ObservationResults
        table_class = DQSWarningListBaseTable

    def get_queryset(self):

        # For older DQS
        if not self.is_new_data_quality_service_active:
            qs = super().get_queryset()
            return qs.add_message()

        # Calling the qs method of DQSWarningListBaseView
        return super(WarningListBaseView, self).get_queryset()

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
