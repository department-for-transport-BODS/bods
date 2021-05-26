from transit_odp.data_quality.tables.slow_timings import (
    SlowTimingWarningTimingTable,
    SlowTimingWarningVehicleTable,
)


class SlowLinkWarningTimingTable(SlowTimingWarningTimingTable):
    class Meta(SlowTimingWarningTimingTable.Meta):
        pass


class SlowLinkWarningVehicleTable(SlowTimingWarningVehicleTable):
    class Meta(SlowTimingWarningVehicleTable.Meta):
        pass
