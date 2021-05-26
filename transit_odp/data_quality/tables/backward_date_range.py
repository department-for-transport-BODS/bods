import django_tables2 as tables
from django.utils.html import format_html

from transit_odp.data_quality.tables.base import (
    JourneyListTable,
    StopNameTimingPatternTable,
    VehicleJourneyTimingPatternTable,
)


class BackwardDateRangeWarningListTable(JourneyListTable):
    line = tables.Column(
        verbose_name="Line",
        orderable=False,
    )

    class Meta(JourneyListTable.Meta):
        pass

    def render_message(self, value, record):
        return format_html(
            """
            <a class="govuk-link" href="{}">{}</div>
            """,
            record.get_absolute_url(),
            record.message,
        )


class BackwardDateRangeWarningDetailTable(VehicleJourneyTimingPatternTable):
    class Meta(StopNameTimingPatternTable.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_message = format_html(self.warning_message)
