import django_tables2 as tables
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from transit_odp.common.tables import GovUkTable
from transit_odp.organisation.tables import FeedStatusColumn, get_feed_name_linkify


class FaresDataFeedTable(GovUkTable):
    status = FeedStatusColumn(show_update_link=False, app_name="fares")
    name = tables.Column(
        verbose_name="Data set name",
        attrs={
            "a": {"class": "govuk-link"},
            "th": {"class": "govuk-table__header", "width": "20%"},
        },
        linkify=lambda record: get_feed_name_linkify(record, app_name="fares"),
        order_by=("live_revision__name"),
    )
    id = tables.Column(verbose_name="Data set ID")
    modified = tables.Column(
        verbose_name="Last updated",
        attrs={
            "th": {"class": "govuk-table__header", "width": "25%"},
        },
    )
    short_description = tables.Column(
        attrs={
            "th": {"class": "govuk-table__header", "width": "20%"},
        },
    )

    class Meta(GovUkTable.Meta):
        attrs = {"th": {"class": "govuk-table__header"}}


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
