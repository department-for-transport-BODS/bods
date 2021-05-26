import django_tables2 as tables
from django.utils.html import format_html

from transit_odp.common.tables import GovUkTable
from transit_odp.data_quality.dataclasses.features import VehicleJourney
from transit_odp.data_quality.tables import WarningListBaseTable


class LineExpiredListTable(WarningListBaseTable):
    line = tables.Column(verbose_name="Line", empty_values=(), orderable=False)
    message = tables.Column(verbose_name="Journey", empty_values=(), orderable=False)

    class Meta(WarningListBaseTable.Meta):
        sequence = ("line", "message")


class LineWarningDetailTable(GovUkTable):
    line = tables.Column(orderable=False)
    journey_date = tables.Column(empty_values=(), orderable=False)
    start_time = tables.TimeColumn(format="H:i", orderable=False)
    first_stop_name = tables.Column(verbose_name="First stop", orderable=False)

    def render_journey_date(self, **kwargs):
        record = kwargs.get("record")
        try:
            date = record.dates[0].strftime("%d/%m/%Y")
        except IndexError:
            date = format_html("&mdash;")
        finally:
            return date

    class Meta(GovUkTable.Meta):
        Model = VehicleJourney
        sequence = ("line", "journey_date", "start_time", "first_stop_name")
        attrs = {
            "caption": {"class": "govuk-heading-m"},
            "th": {"class": "govuk-table__header"},
        }
