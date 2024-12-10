from django.db.models import CharField, OuterRef, Subquery, Value
from django.db.models.functions import Concat

import transit_odp.data_quality.constants as constants
from transit_odp.data_quality.models.transmodel import TimingPatternStop
from transit_odp.data_quality.tables import (
    StopRepeatedWarningDetailTable,
    StopRepeatedWarningListTable,
    StopRepeatedWarningVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class StopRepeatedListView(TimingPatternsListBaseView):
    data = constants.StopsRepeatedObservation
    model = data.model
    table_class = StopRepeatedWarningListTable

    def get_queryset(self):
        qs = super().get_queryset()
        message = " is included multiple times"
        service_name_subquery = TimingPatternStop.objects.filter(
            id=OuterRef("timings")
        ).values_list("service_pattern_stop__stop__name")
        return qs.annotate(
            message=Concat(
                Subquery(service_name_subquery, output_field=CharField()),
                Value(message, output_field=CharField()),
            )
        ).distinct("timing_pattern_id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Following timing pattern(s) have been observed to have the "
                    "same stop multiple times"
                ),
            }
        )
        return context


class StopRepeatedDetailView(TwoTableDetailView):
    data = constants.StopsRepeatedObservation
    model = data.model
    tables = [StopRepeatedWarningDetailTable, StopRepeatedWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name
        stop_name = (
            self.warning.get_effected_stops()
            .values_list("name", flat=True)
            .distinct()
            .first()
        )
        context["title"] = title
        context["subtitle"] = f"Line {line_name}, {stop_name} is found multiple times"
        return context
