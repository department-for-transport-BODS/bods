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
from waffle import flag_is_active

class IncorrectNOCListView(WarningListBaseView):
    data = IncorrectNocObservation
    model = IncorrectNOCWarning
    table_class = IncorrectNOCListTable
    columns = ["observation", "service_code", "line_name", "message", "dqs_details"]
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )

    def get_queryset(self):

        # For older DQS
        if not self.is_new_data_quality_service_active:
            qs = super().get_queryset()
            return qs.add_message()

        report_id = self.kwargs.get("report_id")
        revision_id = self.request.GET.get("revision_id")
        print(f"kwargs: ", self.kwargs)

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
                message=Concat(
                    F(
                        "taskresults__transmodel_txcfileattributes__service_txcfileattributes__name"
                    ),
                    F(
                        "taskresults__transmodel_txcfileattributes__service_code",
                    ),
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
        return qs2

    def get_table_kwargs(self):
        # kwargs = super().get_table_kwargs()
        kwargs = {}
        kwargs.update({"message_col_verbose_name": "Summary", "count": self.row_count})
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
