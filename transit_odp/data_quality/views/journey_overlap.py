from django.db.models import Case, DurationField, When

from transit_odp.data_quality.constants import JourneyOverlapObservation
from transit_odp.data_quality.models.warnings import JourneyConflictWarning
from transit_odp.data_quality.tables import JourneyOverlapWarningTimingTable
from transit_odp.data_quality.tables.base import JourneyLineListTable
from transit_odp.data_quality.views.base import JourneyListBaseView, OneTableDetailView

TIME_FORMAT = "%H:%M:%S"
DATE_FORMAT = "%d/%m/%Y"


class JourneyOverlapListView(JourneyListBaseView):
    data = JourneyOverlapObservation
    model = JourneyConflictWarning
    table_class = JourneyLineListTable

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .add_line()
            .add_message()
            .order_by("vehicle_journey_id")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "The following journey overlap has been observed in following "
                    "journeys."
                ),
            }
        )
        return context


# TODO: refactor -- many methods duplicate TimingDetailBaseView
class JourneyOverlapDetailView(OneTableDetailView):
    data = JourneyOverlapObservation
    model = JourneyConflictWarning
    # awkward to have a MultiTableView with only one table,
    # but maintains similarity with other detail views
    tables = [JourneyOverlapWarningTimingTable]

    def get_warning(self):
        pk = self.kwargs.get("warning_pk")
        select_fields = (
            "conflict__timing_pattern__service_pattern",
            "vehicle_journey__timing_pattern__service_pattern",
        )
        prefetch_fields = (
            (
                "vehicle_journey__timing_pattern__service_pattern__"
                "service_pattern_stops__stop"
            ),
            "conflict__timing_pattern__service_pattern__service_pattern_stops__stop",
            "conflict__timing_pattern__timing_pattern_stops__service_pattern_stop",
        )
        warning = (
            self.model.objects.filter(id=pk)
            .select_related(*select_fields)
            .prefetch_related(*prefetch_fields)
            .get()
        )
        return warning

    @classmethod
    def get_conflict_points(cls, conflict):
        conflict_timing_ps = conflict.timing_pattern.timing_pattern_stops.all()
        conflict_stop_points = [
            (t.service_pattern_stop.stop_id, t.departure) for t in conflict_timing_ps
        ]
        return conflict_stop_points

    # gets only stops from vehicle_journey -- any stops that are different in
    # conflicting journey don't get shown
    # seems to be unavoidable aspect of the design!
    # data required is substantially different to other OneTableDetailView children
    def get_queryset1(self):
        warning = self.warning
        conflict = self.warning.conflict

        # using Case(When()) not ideal because requires list comprehension to create
        # the whens but not sure how to do this as subquery
        conflict_stop_points = self.get_conflict_points(conflict)
        whens = [
            When(service_pattern_stop__stop_id=tps_id, then=departure)
            for tps_id, departure in conflict_stop_points
        ]
        ordering = "service_pattern_stop__position"
        qs = (
            warning.get_timing_pattern()
            .timing_pattern_stops.order_by(ordering)
            .annotate(journey_2_departure=Case(*whens, output_field=DurationField()))
            .add_stop_name()
            .add_position()
        )
        return qs

    @classmethod
    def get_first_stop_name(cls, vehicle_journey):
        """Helper function to get the earliest stop name, assumes that
        service_pattern_stops
        have been prefetched."""
        service_pattern_stops = (
            vehicle_journey.timing_pattern.service_pattern.service_pattern_stops.all()
        )
        earliest = sorted(service_pattern_stops, key=lambda s: s.position)[0]
        return earliest.stop.name

    @property
    def warning_message(self):
        """Helper function to generate the warning message, assumes data has been
        prefetched."""
        warning = self.warning

        if hasattr(self, "_warning_message"):
            return self._warning_message

        start_time_1 = warning.vehicle_journey.start_time.strftime(TIME_FORMAT)
        start_time_2 = warning.conflict.start_time.strftime(TIME_FORMAT)
        from_stop_1 = self.get_first_stop_name(warning.vehicle_journey)
        from_stop_2 = self.get_first_stop_name(warning.conflict)
        first_date = warning.vehicle_journey.dates[0].strftime(DATE_FORMAT)
        self._warning_message = (
            f"{start_time_1} from {from_stop_1} and "
            f"{start_time_2} from {from_stop_2} overlaps on {first_date}"
        )
        return self._warning_message

    @property
    def affected_stops(self):
        if hasattr(self, "_affected_stops"):
            return self._affected_stops
        self._affected_stops = self.warning.get_effected_stops().all()
        return self._affected_stops

    @property
    def affected_stop_ids(self):
        stop_ids = {t.service_pattern_stop.stop_id for t in self.affected_stops}
        return stop_ids

    @property
    def affected_stop_positions(self):
        return [s.position for s in self.affected_stops]

    # table sufficiently different to make it worth
    # entirely re-implementing get_table1_kwargs
    def get_table1_kwargs(self):
        vehicle_journey = self.warning.vehicle_journey
        conflict = self.warning.conflict

        start_time1 = vehicle_journey.start_time.strftime(TIME_FORMAT)
        start_time2 = conflict.start_time.strftime(TIME_FORMAT)
        return {
            "effected_stops": self.affected_stops,
            "effected_stop_positions": self.affected_stop_positions,
            "start_time1": start_time1,
            "start_time2": start_time2,
            "warning_message": self.warning_message,
            "vehicle_journey_warning_start_time": vehicle_journey.start_time,
            "vehicle_journey_conflict_start_time": conflict.start_time,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "subtitle": self.warning_message,
                "effected_stop_ids": ",".join(map(str, self.affected_stop_ids)),
            }
        )
        return context
