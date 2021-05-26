import django_tables2 as tables
import pytz
from django.utils.html import format_html
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.common.tables import GovUkTable, TruncatedTextColumn
from transit_odp.organisation.tables import FeedStatusColumn, get_feed_name_linkify


class DatasetTable(GovUkTable):
    status = FeedStatusColumn(show_update_link=False)
    name = tables.Column(
        verbose_name="Data set name",
        attrs={
            "a": {"class": "govuk-link"},
            "th": {"class": "govuk-table__header", "width": "25%"},
        },
        linkify=lambda record: get_feed_name_linkify(record),
        order_by=("live_revision__name"),
    )
    id = tables.Column(verbose_name="Data set ID")
    modified = tables.Column(verbose_name="Last updated")
    short_description = tables.Column()

    class Meta(GovUkTable.Meta):
        attrs = {"th": {"class": "govuk-table__header"}}

    # Expiry
    def render_first_expiring_service(self, value):
        return format_html(
            """
            <div>{}</div>
            """,
            value.astimezone(pytz.timezone("Europe/London")).strftime(
                "%d %b %Y %I:%M%P"
            ),
        )


class DraftDatasetRevisionTable(DatasetTable):
    draft_revision_name = TruncatedTextColumn(
        verbose_name="Data set",
        attrs={"a": {"class": "govuk-link"}},
        linkify=lambda record: reverse(
            "revision-publish",
            kwargs={"pk": record.dataset.id, "pk1": record.dataset.organisation_id},
            host=config.hosts.PUBLISH_HOST,
        )
        if record.dataset.live_revision is None
        else reverse(
            "revision-update-publish",
            kwargs={"pk": record.dataset.id, "pk1": record.dataset.organisation_id},
            host=config.hosts.PUBLISH_HOST,
        ),
    )

    class Meta(DatasetTable.Meta):
        pass


class DatasetRevisionTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        template_name = "publish/snippets/feed_change_log_table.html"

    comment = tables.Column(verbose_name="Comment", orderable=False)
    status = FeedStatusColumn(show_update_link=False, orderable=False)
    published_at = tables.Column(
        verbose_name="Updated date",
        orderable=False,
    )

    def render_published_at(self, value):
        return format_html(
            """
            <div>{}</div>
            """,
            value.astimezone(pytz.timezone("Europe/London")).strftime("%d %b %Y %H:%M"),
        )
