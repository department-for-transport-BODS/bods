from transit_odp.data_quality.tables.fast_timings import (
    FastTimingWarningTimingTable,
    FastTimingWarningVehicleTable,
)

# Technically these dont need to be defined but defining them anyway to be explicit


class FastLinkWarningTimingTable(FastTimingWarningTimingTable):
    class Meta(FastTimingWarningTimingTable.Meta):
        pass


class FastLinkWarningVehicleTable(FastTimingWarningVehicleTable):
    class Meta(FastTimingWarningVehicleTable.Meta):
        pass
