import django_tables2 as tables

from transit_odp.data_quality.tables import WarningListBaseTable


class IncorrectNOCListTable(WarningListBaseTable):
    message = tables.Column(verbose_name="Service", orderable=False, empty_values=())
    dqs_details = tables.Column(
        verbose_name="Details", orderable=False, empty_values=()
    )

    class Meta(WarningListBaseTable.Meta):
        sequence = ("message", "dqs_details")
