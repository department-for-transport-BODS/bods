from transit_odp.data_quality.tables.base import VehicleJourneyTimingPatternTable


class MissingHeadsignWarningTimingTable(VehicleJourneyTimingPatternTable):
    caption_end = "is missing a destination"

    class Meta(VehicleJourneyTimingPatternTable.Meta):
        pass
