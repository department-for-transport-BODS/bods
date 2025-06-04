import django_tables2 as tables
import pytz
from django.utils.html import format_html
from django_hosts.resolvers import reverse
from waffle import flag_is_active

from config.hosts import PUBLISH_HOST
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.tables import GovUkTable, TruncatedTextColumn
from transit_odp.organisation.tables import FeedStatusColumn, get_feed_name_linkify

COMMENT_ATTRS = {"th": {"class": "govuk-table__header govuk-!-width-one-third"}}


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
    short_description = tables.Column(
        attrs={
            "th": {"class": "govuk-table__header", "width": "20%"},
        },
    )

    class Meta(GovUkTable.Meta):
        attrs = {"th": {"class": "govuk-table__header"}}

    def render_modified(self, value, record=None):
        if record.published_at:
            return record.published_at
        return value

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
        linkify=lambda record: (
            reverse(
                "revision-publish",
                kwargs={"pk": record.dataset.id, "pk1": record.dataset.organisation_id},
                host=PUBLISH_HOST,
            )
            if record.dataset.live_revision is None
            else reverse(
                "revision-update-publish",
                kwargs={"pk": record.dataset.id, "pk1": record.dataset.organisation_id},
                host=PUBLISH_HOST,
            )
        ),
    )

    class Meta(DatasetTable.Meta):
        pass


class DatasetRevisionTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        template_name = "publish/snippets/feed_change_log_table.html"

    comment = tables.Column(
        verbose_name="Comment", orderable=False, attrs=COMMENT_ATTRS
    )
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


class RequiresAttentionColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name = "Timetable services requiring attention"


class AVLRequiresAttentionColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name = "Location services requiring attention"


class FaresRequiresAttentionColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name = "Fares services requiring attention"


class AgentOrganisationsTable(GovUkTable):
    """
    Table displaying all organisations assoicated with an agent along
    with timetables, location and fares data requiring attention.
    """

    class Meta(GovUkTable.Meta):
        attrs = {
            "th": {
                "class": "govuk-table__header govuk-!-width-one-quarter govuk-!-padding-bottom-3"
            },
            "class": "agent_dashboard",
        }

    organisation = tables.Column(
        linkify=lambda value, record: record["next"],
        attrs={
            "td": {"class": "govuk-!-font-weight-bold"},
            "a": {"class": "govuk-link"},
        },
        verbose_name="Organisation",
    )
    requires_attention = RequiresAttentionColumn(empty_values=())
    avl_requires_attention = AVLRequiresAttentionColumn(empty_values=())
    fares_requires_attention = FaresRequiresAttentionColumn(empty_values=())

    def render_organisation(self, value, record):
        # status refers to the name of the css class found here:
        # sass/components/status_indicator/_status_indicator.scss
        is_complete_service_pages_active = flag_is_active(
            "", FeatureFlags.COMPLETE_SERVICE_PAGES.value
        )
        if is_complete_service_pages_active:
            if (
                (record["requires_attention"] > 0)
                or (record["avl_requires_attention"] > 0)
                or (record["fares_requires_attention"] > 0)
            ):
                status = "error"
            else:
                status = "success"
        else:
            if record["requires_attention"] > 0:
                status = "unavailable"
            else:
                status = "success"

        return format_html(
            '<span class="status-indicator status-indicator--{status}"></span> {value}',
            status=status,
            value=value,
        )

    def render_requires_attention(self, value, record):
        requires_attention = record["requires_attention"]
        if requires_attention > 0:
            return format_html(
                "{count} "
                '<a class="govuk-link govuk-!-margin-left-1" href="{href}">'
                "View"
                "</a>",
                count=record["requires_attention"],
                href=reverse(
                    "requires-attention",
                    args=[record["organisation_id"]],
                    host=PUBLISH_HOST,
                ),
            )
        return requires_attention

    def render_avl_requires_attention(self, value, record):
        avl_requires_attention = record["avl_requires_attention"]
        if avl_requires_attention > 0:
            return format_html(
                "{count} "
                '<a class="govuk-link govuk-!-margin-left-1" href={href}>'
                "View"
                "</a>",
                count=record["avl_requires_attention"],
                href=reverse(
                    "avl:requires-attention",
                    args=[record["organisation_id"]],
                    host=PUBLISH_HOST,
                ),
            )
        return avl_requires_attention

    def render_fares_requires_attention(self, value, record):
        fares_requires_attention = record["fares_requires_attention"]
        if fares_requires_attention > 0:
            return format_html(
                "{count} "
                '<a class="govuk-link govuk-!-margin-left-1" href={href}>'
                "View"
                "</a>",
                count=record["fares_requires_attention"],
                href=reverse(
                    "fares:requires-attention",
                    args=[record["organisation_id"]],
                    host=PUBLISH_HOST,
                ),
            )
        else:
            return format_html(
                "{count} ",
                count=record["fares_requires_attention"],
            )
