from transit_odp.data_quality.tables.base import (
    JourneyLineListTable,
    VehicleJourneyTimingPatternTable,
)


class DuplicateJourneyListTable(JourneyLineListTable):
    class Meta(JourneyLineListTable.Meta):
        pass

    def __init__(self, *args, **kwargs):
        # Override init since DataQualityReportSummary double counts duplicates
        # i.e. original + duplicate is 2 journeys but 1 duplicate
        # Deduplication occurs in the queryset so to get the header to show the
        # correct count we just count the queryset and replace the count that
        # comes from the summary.
        qs = kwargs["data"]
        kwargs["count"] = qs.count()
        super().__init__(*args, **kwargs)


class DuplicateJourneyWarningTimingTable(VehicleJourneyTimingPatternTable):
    caption_end = "is included in your data more than once."

    class Meta(VehicleJourneyTimingPatternTable.Meta):
        pass
