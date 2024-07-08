import django_tables2 as tables

from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    TimingPatternListTable,
    VehicleJourneyTable,
)


class StopMissingNaptanListTable(TimingPatternListTable):
    line = tables.Column(
        verbose_name="Line",
        orderable=False,
    )

    class Meta(TimingPatternListTable.Meta):
        sequence = ("line", "message")


class StopMissingNaptanWarningTimingTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        self.warning_message = kwargs.pop("warning_message")
        super().__init__(*args, **kwargs)

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class StopMissingNaptanWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
