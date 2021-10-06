import django_tables2 as tables

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
