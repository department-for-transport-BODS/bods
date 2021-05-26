import django_tables2 as tables
from django.utils.html import format_html

from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    TimingPatternListTable,
    VehicleJourneyTable,
)


class StopIncorrectTypeListTable(TimingPatternListTable):
    line = tables.Column(
        verbose_name="Line",
        orderable=False,
    )
    message = tables.Column(
        verbose_name="Timing pattern",
        empty_values=(),
        orderable=False,
    )

    class Meta(TimingPatternListTable.Meta):
        sequence = ("line", "message")

    def render_message(self, record, value):
        return format_html(
            """
            <a class="govuk-link" href="{}">{}</div>
            """,
            record.get_absolute_url(),
            record.message,
        )


class StopIncorrectTypeWarningTimingTable(StopNameTimingPatternTable):
    stop_type = tables.Column(orderable=False)

    def __init__(self, *args, **kwargs):
        self.warning_message = kwargs.pop("warning_message")
        super().__init__(*args, **kwargs)

    class Meta(StopNameTimingPatternTable.Meta):
        sequence = ("arrival", "departure", "stop_type", "name")


class StopIncorrectTypeWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
