import datetime

import django_tables2 as tables
from django.utils.html import format_html

from transit_odp.data_quality.tables.base import StopNameTimingPatternTable


class JourneyOverlapWarningTimingTable(StopNameTimingPatternTable):
    title = "Vehicle journey"

    # TODO: Replace this very hacky way of overriding the two colummns!
    # (did originally try inheritance, but the unwanted fields kept appearing even
    # when specifying fields in the Meta)
    arrival = tables.Column(
        accessor="departure",
        orderable=False,
        # Backup verbose name, in case departure time not available
        verbose_name="Journey Departure 1",
        attrs={"th": {"class": "govuk-table__header govuk-!-width-one-quarter"}},
    )
    departure = tables.Column(
        accessor="journey_2_departure",
        orderable=False,
        # Backup verbose name, in case departure time not available
        verbose_name="Journey Departure 2",
        empty_values=(None, ""),
        default=format_html("&mdash;"),
        attrs={"th": {"class": "govuk-table__header govuk-!-width-one-quarter"}},
    )

    class Meta(StopNameTimingPatternTable.Meta):
        pass

    def __init__(self, *args, **kwargs):
        start_time1 = kwargs.pop("start_time1", None)
        start_time2 = kwargs.pop("start_time2", None)
        self.vehicle_journey_warning_start_time = kwargs.pop(
            "vehicle_journey_warning_start_time"
        )
        self.vehicle_journey_conflict_start_time = kwargs.pop(
            "vehicle_journey_conflict_start_time"
        )

        warning_message = kwargs.pop("warning_message")

        if start_time1:
            self.base_columns[
                "arrival"
            ].verbose_name = f"{start_time1} Journey Departure"
        if start_time2:
            self.base_columns[
                "departure"
            ].verbose_name = f"{start_time2} Journey Departure"

        super().__init__(*args, **kwargs)
        self.warning_message = warning_message

    def render_arrival(self, value, record):
        # Note this is departure 1, we should fix this table
        journey_start_time = self.vehicle_journey_warning_start_time
        return self._convert_to_absolute_time(value, journey_start_time)

    def render_departure(self, value, record):
        journey_start_time = self.vehicle_journey_conflict_start_time
        return self._convert_to_absolute_time(value, journey_start_time)

    # copied from VehicleJourneyTimingPatternTable and tweaked
    def _convert_to_absolute_time(self, value, journey_start_time):
        # arbitrary date -- we only need date to create a valid datetime object
        # (only time used in frontend)
        date = datetime.date(1900, 1, 1)
        time = journey_start_time
        datetime_obj = datetime.datetime.combine(date, time)
        total = datetime_obj + value
        return total.time().isoformat()
