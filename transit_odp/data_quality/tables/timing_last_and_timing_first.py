from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    VehicleJourneyTable,
)


class TimingLastWarningDetailTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_message = (
            f"{self.last_effected_stop.name} is the last stop in a timing "
            "pattern but is not designated a timing point"
        )

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class TimingLastWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass


class TimingFirstWarningDetailTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_message = (
            f"{self.first_effected_stop.name} is the first stop in a timing "
            "pattern but is not designated a timing point"
        )

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class TimingFirstWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
