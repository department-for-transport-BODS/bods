from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    VehicleJourneyTable,
)


class ServiceLinkMissingStopWarningTimingTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        self.warning_message = kwargs.pop("warning_message")
        super().__init__(*args, **kwargs)

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class ServiceLinkMissingStopWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
