import django_tables2 as tables
from django.utils.html import format_html

from transit_odp.common.tables import GovUkTable
from transit_odp.data_quality.tables.base import (
    BaseStopNameTimingPatternTable,
    TimingPatternListTable,
    VehicleJourneyTable,
)


class BackwardTimingsListTable(TimingPatternListTable):
    message = tables.Column(
        verbose_name="Timing pattern", orderable=False, empty_values=()
    )

    def render_message(self, value, record):
        first_effected_stop = record.from_stop.service_pattern_stop.stop.name
        last_effected_stop = record.to_stop.service_pattern_stop.stop.name
        message = (
            f"Backward timing between {first_effected_stop} and {last_effected_stop}"
        )

        return format_html(
            """
            <a class="govuk-link" href="{}">{}</div>
            """,
            record.get_absolute_url(),
            message,
        )

    # If leave out Meta, formatting goes weird even though it's inheriting from
    # JourneyListTable
    class Meta(GovUkTable.Meta):
        sequence = ("line", "message")


class BackwardTimingsWarningTable(BaseStopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        self.effected_stop_positions = list(kwargs.pop("effected_stop_positions"))
        self.first_effected_stop, self.last_effected_stop = kwargs.pop("effected_stops")
        self.warning_message = (
            f"Backward timing was detected between "
            f"{self.first_effected_stop.service_pattern_stop.stop.name} and "
            f"{self.last_effected_stop.service_pattern_stop.stop.name}"
        )
        row_attrs = {
            "class": lambda record: "effected"
            if record.position in self.effected_stop_positions
            else ""
        }
        super().__init__(*args, row_attrs=row_attrs, **kwargs)

    class Meta(BaseStopNameTimingPatternTable.Meta):
        pass


class BackwardTimingVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
