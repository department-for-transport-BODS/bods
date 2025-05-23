from math import floor

import django_tables2 as tables
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from transit_odp.avl.constants import PENDING
from transit_odp.avl.post_publishing_checks.constants import NO_PPC_DATA
from transit_odp.common.tables import GovUkTable
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.tables import FeedStatusColumn, get_feed_name_linkify


class AVLDataFeedTable(GovUkTable):
    status = FeedStatusColumn(show_update_link=False, app_name="avl")
    percent_matching = tables.Column(verbose_name="AVL to Timetable matching")
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

    def render_percent_matching(self, value, record):
        if record.status in [FeedStatus.expired.value, FeedStatus.inactive.value]:
            return ""
        if value == float(NO_PPC_DATA):
            return PENDING
        return str(int(floor(value))) + "%"


class AVLLineColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name = "Line"
        self.attrs["annotation"] = mark_safe(
            render_to_string("publish/snippets/help_modals/line_service_number.html")
        )


class AVLRequiresAttentionTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        pass

    licence_number = tables.Column(verbose_name="Licence number")
    service_code = tables.Column(verbose_name="Service code")
    line_number = AVLLineColumn(verbose_name="Line", accessor="line_number")
