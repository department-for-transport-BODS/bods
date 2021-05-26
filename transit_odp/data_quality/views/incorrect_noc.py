from transit_odp.data_quality.constants import IncorrectNocObservation
from transit_odp.data_quality.models.warnings import IncorrectNOCWarning
from transit_odp.data_quality.tables.incorrect_noc import IncorrectNOCListTable
from transit_odp.data_quality.views.base import WarningListBaseView


class IncorrectNOCListView(WarningListBaseView):
    data = IncorrectNocObservation
    model = IncorrectNOCWarning
    table_class = IncorrectNOCListTable

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.add_message()

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs.update({"message_col_verbose_name": "Summary"})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following data sets have been observed to have incorrect "
                    "national operator code(s)."
                ),
            }
        )
        return context
