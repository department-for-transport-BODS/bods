from transit_odp.data_quality.tables import (
    StopNameTimingPatternTable,
    TimingPatternListTable,
    VehicleJourneyTable,
)


class MissingStopWarningListTable(TimingPatternListTable):
    class Meta(TimingPatternListTable.Meta):
        pass


class MissingStopWarningDetailTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.warning_message = (
            f"Next timing point after "
            f"{self.first_effected_stop.name} is missing or "
            f"is greater than 15 minutes away"
        )

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class MissingStopWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
