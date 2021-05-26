from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    VehicleJourneyTable,
)


class SlowTimingWarningTimingTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_message = (
            "Timing pattern requires travel between "
            f"{self.first_effected_stop.name} and "
            f"{self.last_effected_stop.name} under 1mph"
        )

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class SlowTimingWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
