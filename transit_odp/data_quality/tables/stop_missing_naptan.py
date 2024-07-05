import django_tables2 as tables

from transit_odp.data_quality.tables.base import (
    StopNameTimingPatternTable,
    TimingPatternListTable,
    VehicleJourneyTable,
)
from waffle import flag_is_active

class StopMissingNaptanListTable(TimingPatternListTable):

    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )

    if is_new_data_quality_service_active:
        message = tables.Column(
            verbose_name="Service", orderable=False, empty_values=()
        )
        dqs_details = tables.Column(
            verbose_name="Details",
            orderable=False,
            empty_values=(),
            attrs={"is_link": True},
        )
        service_code = tables.Column(verbose_name="Service Code", visible=True)
        line_name = tables.Column(verbose_name="Line Name", visible=True)
    else:
        line = tables.Column(
            verbose_name="Line",
            orderable=False,
        )

    class Meta(TimingPatternListTable.Meta):
        is_new_data_quality_service_active = flag_is_active(
            "", "is_new_data_quality_service_active"
        )

        if is_new_data_quality_service_active:
            attrs = {
                "tbody": {"is_details_link": True},
            }
        sequence = ("line", "message")


class StopMissingNaptanWarningTimingTable(StopNameTimingPatternTable):
    def __init__(self, *args, **kwargs):
        self.warning_message = kwargs.pop("warning_message")
        super().__init__(*args, **kwargs)

    class Meta(StopNameTimingPatternTable.Meta):
        pass


class StopMissingNaptanWarningVehicleTable(VehicleJourneyTable):
    class Meta(VehicleJourneyTable.Meta):
        pass
