from transit_odp.data_quality.constants import IncorrectNocObservation, Checks
from transit_odp.data_quality.models.warnings import IncorrectNOCWarning
from transit_odp.data_quality.tables.incorrect_noc import IncorrectNOCListTable
from transit_odp.data_quality.views.base import WarningListBaseView
from transit_odp.dqs.models import ObservationResults
from django.db.models.functions import Concat  # type: ignore
from django.db.models import F
import pandas as pd
from django.db.models.expressions import Func, RawSQL, Value
from django.db.models import CharField, F, OuterRef, Subquery, TextField

class IncorrectNOCListView(WarningListBaseView):
    data = IncorrectNocObservation
    model = IncorrectNOCWarning
    table_class = IncorrectNOCListTable
    columns = ["observation", "service_code", "line_name", "message", "dqs_details"]

    def get_queryset(self):
        qs = super().get_queryset()
        report_id = self.kwargs.get("report_id")
        revision_id = self.request.GET.get("revision_id")
        print(f"kwargs: ", self.kwargs)
        # print(f"request: ", self.request.GET)
        print(f"Query: {qs.query}")

        qs2 = (
            ObservationResults.objects.filter(
                taskresults__dataquality_report_id=report_id,
                taskresults__checks__observation=Checks.IncorrectNoc.value,
                taskresults__transmodel_txcfileattributes__id=365,
            )
            .annotate(
                observation=F("taskresults__checks__observation"),
                service_code=F(
                    "taskresults__transmodel_txcfileattributes__service_code"
                ),
                line_name=F(
                    "taskresults__transmodel_txcfileattributes__service_txcfileattributes__name"
                ),
                message=Concat(F(
                    "taskresults__transmodel_txcfileattributes__service_txcfileattributes__name"
                ),
                dqs_details=Concat(
                    F(
                        "taskresults__transmodel_txcfileattributes__service_code",
                    ),
                    Value(
                        " is specified in the dataset but not assigned to your "
                        "organisation",
                        output_field=TextField(),
                    ),
                    output_field=TextField(),
                ),
            )
            .values(*self.columns)
        )
        pd.set_option("display.max_rows", 500)
        pd.set_option("display.max_columns", 500)
        df = pd.DataFrame.from_records(qs2)
        print(df)
        print("New query: ", qs2.query)
        return qs2
        return qs.add_message()

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs.update({"message_col_verbose_name": "Summary", "count": 1})
        print(f"kwargs: {kwargs}")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "resolve": self.data.resolve,
                "preamble": (
                    "The following data sets have been observed to have incorrect "
                    "national operator code(s)."
                ),
            }
        )
        return context
