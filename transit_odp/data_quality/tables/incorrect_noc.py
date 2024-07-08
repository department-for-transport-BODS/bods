import django_tables2 as tables

from transit_odp.data_quality.tables import WarningListBaseTable
from waffle import flag_is_active


class IncorrectNOCListTable(WarningListBaseTable):
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
        )
        service_code = tables.Column(verbose_name="Service Code", visible=True)
        line_name = tables.Column(verbose_name="Line Name", visible=True)
    else:
        message = tables.Column(
            verbose_name="Summary", orderable=False, empty_values=()
        )

    class Meta(WarningListBaseTable.Meta):
        is_new_data_quality_service_active = flag_is_active(
            "", "is_new_data_quality_service_active"
        )
        sequence = (
            ("message", "dqs_details")
            if is_new_data_quality_service_active
            else ("message",)
        )
