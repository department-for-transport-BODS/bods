import datetime

import django_tables2 as tables
from django.utils.html import format_html

from transit_odp.common.tables import GovUkTable
from transit_odp.data_quality.helpers import convert_date_to_dmY_string
from transit_odp.data_quality.models.transmodel import (
    ServicePatternStop,
    VehicleJourney,
)


class BaseStopNameTimingPatternTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        template_name = "data_quality/snippets/dq_custom_table_boxed.html"
        Model = ServicePatternStop
        sequence = ("arrival", "departure", "name")
        attrs = {
            "th": {"class": "govuk-table__header"},
        }

    table_pagination = False
    pagination_bottom = False
    title = "Timing pattern"
    extra_info = "Stops marked with * are timing points"

    arrival = tables.Column(orderable=False)
    departure = tables.Column(orderable=False)
    name = tables.Column(orderable=False, verbose_name="Stop name")
    position = tables.Column(visible=False)

    def render_name(self, **kwargs):
        record = kwargs["record"]
        value = kwargs["value"]
        return f"*{value}" if record.timing_point else value


class StopNameTimingPatternTable(BaseStopNameTimingPatternTable):
    class Meta(BaseStopNameTimingPatternTable.Meta):
        pass

    def __init__(self, *args, **kwargs):
        try:
            # can use None as default in pop and check for Nones, but EAFP
            self.effected_stop_positions = list(kwargs.pop("effected_stop_positions"))
            self.effected_stops = kwargs.pop("effected_stops")
        except KeyError:
            row_attrs = None
        else:
            self.first_effected_stop = self.effected_stops.earliest("position")
            self.last_effected_stop = self.effected_stops.latest("position")
            row_attrs = {
                "class": lambda record: "effected"
                if record.position in list(self.effected_stop_positions)
                else ""
            }
        finally:
            super().__init__(*args, row_attrs=row_attrs, **kwargs)


class VehicleJourneyTimingPatternTable(StopNameTimingPatternTable):
    title = "Vehicle journey"
    caption_end = ""

    def __init__(self, *args, **kwargs):
        message_segment = kwargs.pop("message_segment")
        self.warning_message = f"{message_segment} {self.caption_end}"
        self.vehicle_journey_start_time = kwargs.pop("vehicle_journey_start_time")
        super().__init__(*args, **kwargs)

    class Meta(StopNameTimingPatternTable.Meta):
        pass

    def _convert_to_absolute_time(self, value):
        # arbitrary date -- we only need date to create a valid datetime object
        # (only time used in frontend)
        date = datetime.date(1900, 1, 1)
        time = self.vehicle_journey_start_time
        datetime_obj = datetime.datetime.combine(date, time)
        total = datetime_obj + value
        return total.time().isoformat()

    def render_arrival(self, value, record):
        return self._convert_to_absolute_time(value)

    def render_departure(self, value, record):
        return self._convert_to_absolute_time(value)


class VehicleJourneyTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        template_name = "data_quality/snippets/dq_custom_table.html"
        Model = VehicleJourney
        sequence = ("line", "journey_date", "start_time", "first_stop_name")
        attrs = {
            "caption": {"class": "govuk-heading-m"},
            "th": {"class": "govuk-table__header"},
        }

    # Hacky -- must be None to ensure default pagination behaviour
    table_pagination = None
    pagination_top = False
    pagination_bottom = True
    # pagination on multi-table pages doesn't work without table name in query
    # params (e.g "?table_1-page=1"). But unless we define prefixed_page_field,
    # paginator will try to use urls like "?page=1", causing odd pagination behaviour
    # TODO: replace hardcoded value -- hardcoding will cause problems if we change
    # table naming
    prefixed_page_field = "table_1-page"

    line = tables.Column(orderable=False)
    journey_date = tables.Column(empty_values=(), orderable=False)
    # Uses Django's time template tag formatting:
    # https://docs.djangoproject.com/en/2.2/ref/templates/builtins/#time
    start_time = tables.TimeColumn(format="H:i", orderable=False)
    first_stop_name = tables.Column(verbose_name="First stop", orderable=False)

    def render_journey_date(self, **kwargs):
        record = kwargs.get("record")
        # TODO: remove the try -- temporarily necessary because not all of our test
        # data have dates
        try:
            date = record.dates[0]
            date = convert_date_to_dmY_string(date)
        except IndexError:
            date = format_html("&mdash;")
        finally:
            return date


class WarningListBaseTable(GovUkTable):
    class Meta:
        template_name = "data_quality/snippets/dqs_custom_table.html"
        attrs = {
            "th": {"class": "govuk-table__header"},
        }

    pagination_bottom = True

    def __init__(self, *args, **kwargs):
        count = kwargs.pop("count", None)
        message_col_verbose_name = kwargs.pop("message_col_verbose_name", None)

        # Don't use existing value of column verbose_name (e.g.
        # with += f' ({count})'. Appends count on every page refresh, so end up with
        # "Journey (4) (4) (4)"
        if message_col_verbose_name and count:
            self.base_columns[
                "message"
            ].verbose_name = f"{message_col_verbose_name} ({count})"

        super().__init__(*args, **kwargs)


class TimingPatternListTable(WarningListBaseTable):
    line = tables.Column(
        verbose_name="Line",
        orderable=False,
    )
    message = tables.Column(
        verbose_name="Timing pattern", orderable=False, linkify=True
    )

    class Meta(WarningListBaseTable.Meta):
        sequence = ("line", "message")


class JourneyLineListTable(WarningListBaseTable):
    line = tables.Column(
        verbose_name="Line",
        orderable=False,
    )
    message = tables.Column(
        verbose_name="Journey",
        empty_values=(),
        orderable=False,
    )

    class Meta(WarningListBaseTable.Meta):
        sequence = ("line", "message")

    def render_message(self, value, record):
        return format_html(
            """
            <a class="govuk-link" href="{}">{}</a>
            """,
            record.get_absolute_url(),
            record.message,
        )


class JourneyListTable(WarningListBaseTable):
    message_end = ""

    line = tables.Column(
        accessor="vehicle_journey__timing_pattern__service_pattern__service__name",
        verbose_name="Line",
        orderable=False,
    )
    message = tables.Column(
        verbose_name="Journey",
        empty_values=(),
        orderable=False,
    )

    class Meta(WarningListBaseTable.Meta):
        sequence = ("line", "message")

    def render_message(self, value, record):
        start_time = record.vehicle_journey.start_time.strftime("%H:%M")
        # TODO: stop picking arbitrary date
        date = self.get_date_string_or_unknown(record.vehicle_journey)
        message = "{start_time} from {first_stop} on {date} {message_end}".format(
            start_time=start_time,
            first_stop=record.first_stop_name,
            date=date,
            message_end=self.message_end,
        )

        return format_html(
            """
            <a class="govuk-link" href="{}">{}</a>
            """,
            record.get_absolute_url(),
            message,
        )

    def get_date_string_or_unknown(self, vehicle_journey):
        try:
            date = vehicle_journey.dates[0]
            date = convert_date_to_dmY_string(date)
        except IndexError:
            date = "unknown date"
        finally:
            return date
