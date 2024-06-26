import django_tables2 as tables

from transit_odp.data_quality.tables import WarningListBaseTable


class IncorrectNOCListTable(WarningListBaseTable):
    message = tables.Column(verbose_name="Service", orderable=False, empty_values=())
    dqs_details = tables.Column(
        verbose_name="Details",
        orderable=False,
        empty_values=(),
    )
    service_code = tables.Column(verbose_name="Service Code", visible=True)
    line_name = tables.Column(verbose_name="Line Name", visible=True)

    class Meta(WarningListBaseTable.Meta):
        sequence = ("message", "dqs_details")
