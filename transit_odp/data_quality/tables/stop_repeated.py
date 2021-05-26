from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    TimingPatternListTable,
    VehicleJourneyTable,
)


class StopRepeatedWarningListTable(TimingPatternListTable):
    class Meta(TimingPatternListTable.Meta):
        pass


class StopRepeatedWarningDetailTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        count = self.effected_stops.count()
        self.warning_message = (
            f"{self.first_effected_stop.name} is repeated {count} times on a route"
        )

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class StopRepeatedWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
