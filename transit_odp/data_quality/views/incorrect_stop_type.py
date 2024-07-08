from django.db.models import F

from transit_odp.data_quality.constants import IncorrectStopTypeObservation
from transit_odp.data_quality.models.warnings import JourneyStopInappropriateWarning
from transit_odp.data_quality.tables import (
    StopIncorrectTypeListTable,
    StopIncorrectTypeWarningTimingTable,
    StopIncorrectTypeWarningVehicleTable,
)
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable
from transit_odp.data_quality.views.base import JourneyListBaseView, TwoTableDetailView
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks
from waffle import flag_is_active

class IncorrectStopTypeListView(JourneyListBaseView):
    data = IncorrectStopTypeObservation
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )

    if not is_new_data_quality_service_active:
        model = JourneyStopInappropriateWarning
        table_class = StopIncorrectTypeListTable
    else:
        model = ObservationResults
        table_class = DQSWarningListBaseTable

    def get_queryset(self):

        if not self.is_new_data_quality_service_active:
            return super().get_queryset().add_line().add_message()

        report_id = self.kwargs.get("report_id")
        revision_id = self.kwargs.get("pk")
        check = Checks.IncorrectStopType
        message = "There is at least one stop with an incorrect stop type"
        return self.model.objects.get_observations_grouped(
            report_id, check, revision_id, message
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following service(s) have been observed to not have the correct stop type."
                ),
                "extra_info": self.data.extra_info,
                "resolve": self.data.resolve,
            }
        )
        return context

    def get_table_kwargs(self):

        kwargs = {}
        if not self.is_new_data_quality_service_active:
            kwargs = super().get_table_kwargs()
        return kwargs


class IncorrectStopTypeDetailView(TwoTableDetailView):
    data = IncorrectStopTypeObservation
    model = JourneyStopInappropriateWarning
    tables = [StopIncorrectTypeWarningTimingTable, StopIncorrectTypeWarningVehicleTable]

    def get_queryset1(self):
        stops_with_name_and_position = super().get_queryset1()
        # TODO: add as queryset method?
        return stops_with_name_and_position.annotate(
            stop_type=F("service_pattern_stop__stop__type")
        )

    def get_table1_kwargs(self):
        kwargs = super().get_table1_kwargs()
        stop = self.warning.stop
        stop_type = self.warning.stop_type
        kwargs[
            "warning_message"
        ] = f"Journeys are using {stop.name} of type {stop_type}"
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warning = self.warning
        stop = warning.stop
        stop_type = warning.stop_type
        # TODO: add get_service_name method to one of the parent models?
        service_name = warning.get_timing_pattern().service_pattern.service.name

        context["title"] = self.data.title
        context[
            "subtitle"
        ] = f'Line {service_name} Uses stop {stop.name} of type "{stop_type}"'
        return context
