from math import floor

import django_tables2 as tables
from django.utils.html import format_html

from transit_odp.avl.constants import (
    MORE_DATA_NEEDED,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
    UNDERGOING,
)
from transit_odp.avl.post_publishing_checks.constants import NO_PPC_DATA
from transit_odp.common.tables import GovUkTable
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.tables import FeedStatusColumn, get_feed_name_linkify


class AVLDataFeedTable(GovUkTable):
    status = FeedStatusColumn(show_update_link=False, app_name="avl")
    avl_compliance_status_cached = tables.Column(verbose_name="BODS compliant data")
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
    short_description = tables.Column(
        attrs={"th": {"class": "govuk-table__header", "width": "25%"}}
    )

    class Meta(GovUkTable.Meta):
        attrs = {"th": {"class": "govuk-table__header"}}

    def render_avl_compliance_status_cached(self, value):
        if value in [NON_COMPLIANT, PARTIALLY_COMPLIANT]:
            return format_html('<i class="fas fa-info-circle"></i> {}', value)
        else:
            return value

    def render_percent_matching(self, value, record):
        if record.status in [FeedStatus.expired.value, FeedStatus.inactive.value]:
            return ""
        if record.avl_compliance_status_cached == MORE_DATA_NEEDED:
            return MORE_DATA_NEEDED
        if value == float(NO_PPC_DATA):
            return UNDERGOING
        return str(int(floor(value))) + "%"
