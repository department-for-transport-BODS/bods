import django_tables2 as tables

from transit_odp.common.tables import GovUkTable
from transit_odp.organisation.tables import FeedStatusColumn, get_feed_name_linkify


class AVLDataFeedTable(GovUkTable):
    status = FeedStatusColumn(show_update_link=False, app_name="avl")
    name = tables.Column(
        verbose_name="Data feed name",
        attrs={
            "a": {"class": "govuk-link"},
            "th": {"class": "govuk-table__header", "width": "25%"},
        },
        linkify=lambda record: get_feed_name_linkify(record, app_name="avl"),
        order_by=("live_revision__name"),
    )
    id = tables.Column(verbose_name="Data feed ID")
    avl_feed_last_checked = tables.Column(verbose_name="Last automated update")
    short_description = tables.Column()

    class Meta(GovUkTable.Meta):
        attrs = {"th": {"class": "govuk-table__header"}}
