from transit_odp.data_quality.constants import MissingHeadsignObservation
from transit_odp.data_quality.models.warnings import JourneyWithoutHeadsignWarning
from transit_odp.data_quality.tables import MissingHeadsignWarningTimingTable
from transit_odp.data_quality.tables.base import JourneyLineListTable
from transit_odp.data_quality.views.base import JourneyListBaseView, OneTableDetailView


class MissingHeadsignListView(JourneyListBaseView):
    data = MissingHeadsignObservation
    model = JourneyWithoutHeadsignWarning
    table_class = JourneyLineListTable

    def get_queryset(self):
        return super().get_queryset().add_first_stop().add_line().add_message()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following journeys have been observed to have missing "
                    "destination display."
                ),
            }
        )
        return context


class MissingHeadsignDetailView(OneTableDetailView):
    data = MissingHeadsignObservation
    model = JourneyWithoutHeadsignWarning
    # awkward to have a MultiTableView with only one table,
    # but maintains similarity with other detail views
    tables = [MissingHeadsignWarningTimingTable]

    def get_context_data(self, **kwargs):
        kwargs.update({"subtitle": self.generate_subtitle()})
        context = super().get_context_data(**kwargs)
        return context

    def generate_subtitle(self):
        vehicle_journey = self.warning.get_vehicle_journey()
        service_name = vehicle_journey.timing_pattern.service_pattern.service.name
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
        return (
            f"{service_name} - {start_time} from {from_stop} is missing a "
            f"destination display"
        )
