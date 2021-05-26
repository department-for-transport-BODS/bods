from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    VehicleJourneyTable,
)


class FastTimingWarningTimingTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_message = (
            f"Timing pattern requires travel "
            f"between {self.first_effected_stop.name} and "
            f"{self.last_effected_stop.name} over a speed of 70 mph."
        )

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class FastTimingWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
