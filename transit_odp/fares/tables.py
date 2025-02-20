import django_tables2 as tables
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from transit_odp.common.tables import GovUkTable


class FaresLineColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name = "Line"
        self.attrs["annotation"] = mark_safe(
            render_to_string("publish/snippets/help_modals/line_service_number.html")
        )


class FaresRequiresAttentionTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        pass

    licence_number = tables.Column(verbose_name="Licence number")
    service_code = tables.Column(verbose_name="Service code")
    line_number = FaresLineColumn(verbose_name="Line", accessor="line_number")
