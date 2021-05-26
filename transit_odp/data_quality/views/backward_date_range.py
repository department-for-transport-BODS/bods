from transit_odp.data_quality.constants import BackwardDateRangeObservation
from transit_odp.data_quality.helpers import (
    convert_date_to_dmY_string,
    create_comma_separated_string,
)
from transit_odp.data_quality.models.warnings import JourneyDateRangeBackwardsWarning
from transit_odp.data_quality.tables import (
    BackwardDateRangeWarningDetailTable,
    BackwardDateRangeWarningListTable,
)
from transit_odp.data_quality.views.base import JourneyListBaseView, OneTableDetailView


class BackwardDateRangeListView(JourneyListBaseView):
    data = BackwardDateRangeObservation
    model = JourneyDateRangeBackwardsWarning
    table_class = BackwardDateRangeWarningListTable

    def get_queryset(self):
        return super().get_queryset().add_line().add_message()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following journeys has been observed to have backward "
                    "date range."
                ),
            }
        )
        return context


class BackwardDateRangeDetailView(OneTableDetailView):
    data = BackwardDateRangeObservation
    model = JourneyDateRangeBackwardsWarning
    tables = [BackwardDateRangeWarningDetailTable]

    def get_context_data(self, **kwargs):
        stop_ids = self.warning.get_stop_ids()
        service_pattern_id = self.warning.get_timing_pattern().service_pattern.id
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "subtitle": self.construct_subtitle(),
                "service_pattern_id": service_pattern_id,
                "stop_ids": create_comma_separated_string(stop_ids),
            }
        )
        return context

    # only used in table for this view, but overriding method allows use of inherited
    # get_table1_kwargs
    def construct_shared_message_segment(self):
        vehicle_journey = self.warning.get_vehicle_journey()
        start_time = vehicle_journey.start_time.strftime("%H:%M")
        # fmt: off
        from_stop = (
            vehicle_journey
            .timing_pattern
            .service_pattern
            .service_pattern_stops
            .earliest("position")
            .stop.name
        )
        # fmt: on
        start = convert_date_to_dmY_string(self.warning.start)
        end = convert_date_to_dmY_string(self.warning.end)
        return (
            f"{start_time} from {from_stop} is scheduled to start on "
            f"{self.boldify(start)} and end on {self.boldify(end)}."
        )

    def construct_subtitle(self, **kwargs):
        vehicle_journey = self.warning.vehicle_journey
        line = vehicle_journey.timing_pattern.service_pattern.service.name
        start_time = vehicle_journey.start_time.strftime("%H:%M")
        # fmt: off
        from_stop = (
            vehicle_journey
            .timing_pattern
            .service_pattern
            .service_pattern_stops
            .earliest("position")
            .stop.name
        )
        # fmt: on
        # TODO: stop using arbitrary date
        start = convert_date_to_dmY_string(self.warning.start)
        return (
            f"Line {line} - {start_time} from {from_stop} on {start} has a backward "
            f"date range"
        )

    def boldify(self, text):
        html = f'<span class="govuk-!-font-weight-bold">{text}</span>'
        return html
