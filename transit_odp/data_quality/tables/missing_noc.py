import django_tables2 as tables

from transit_odp.data_quality.tables import WarningListBaseTable


class MissingNOCListTable(WarningListBaseTable):
    message = tables.Column(verbose_name="Summary", orderable=False, empty_values=())

    class Meta(WarningListBaseTable.Meta):
        sequence = ("message",)
