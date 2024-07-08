import django_tables2 as tables

from transit_odp.data_quality.tables.base import (
    BaseStopNameTimingPatternTable,
    TimingPatternListTable,
    DQSWarningListBaseTable,
    VehicleJourneyTable,
)
from waffle import flag_is_active


class PickUpDropOffListTable(TimingPatternListTable):

    line = tables.Column(verbose_name="Line", orderable=False)

    class Meta(TimingPatternListTable.Meta):

        sequence = ("line", "message")


class LastStopPickUpOnlyDetail(BaseStopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        row_attrs = {
            "class": lambda record: "effected"
            if record.position in list(self.effected_stop_positions)
            else ""
        }
        kwargs.pop("effected_stop_positions", None)
        self.effected_stops = kwargs.pop("effected_stops")
        self.last_effected_stop = self.effected_stops.latest("position")
        self.effected_stop_positions = [self.last_effected_stop.position]
        self.warning_message = (
            f"{self.last_effected_stop.name} is the last "
            "stop in a timing pattern but is designated as pick up only"
        )
        super().__init__(*args, row_attrs=row_attrs, **kwargs)

    class Meta(BaseStopNameTimingPatternTable.Meta):
        pass


class FirstStopDropOffOnlyDetail(BaseStopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        row_attrs = {
            "class": lambda record: "effected"
            if record.position in list(self.effected_stop_positions)
            else ""
        }
        kwargs.pop("effected_stop_positions", None)
        self.effected_stops = kwargs.pop("effected_stops")
        self.first_effected_stop = self.effected_stops.earliest("position")
        self.effected_stop_positions = [self.first_effected_stop.position]
        self.warning_message = (
            f"{self.first_effected_stop.name} is "
            "the first stop in a timing pattern but is designated as set down only"
        )
        super().__init__(*args, row_attrs=row_attrs, **kwargs)

    class Meta(BaseStopNameTimingPatternTable.Meta):
        pass


class LastStopPickUpOnlyVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass


class FirstStopDropOffOnlyVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
