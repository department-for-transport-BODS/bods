from transit_odp.data_quality.constants import MissingNOCCode
from transit_odp.data_quality.models.warnings import MissingNOCWarning
from transit_odp.data_quality.tables.missing_noc import MissingNOCListTable
from transit_odp.data_quality.views.base import WarningListBaseView


class MissingNOCListView(WarningListBaseView):
    data = MissingNOCCode
    model = MissingNOCWarning
    table_class = MissingNOCListTable

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.add_message()

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs.update({"message_col_verbose_name": "Summary"})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": self.data.title, "definition": self.data.text})
        return context
