import django_tables2 as tables
import pytz
from django.core.paginator import Paginator
from django.utils.functional import LazyObject
from django.utils.html import format_html
from django_hosts.resolvers import reverse

import config
from transit_odp.common.tables import GovUkTable, TruncatedTextColumn
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models.data import Dataset
from transit_odp.organisation.tables import FeedStatusColumn
from transit_odp.users.constants import DATASET_MANAGE_TABLE_PAGINATE_BY


def get_absolute_url(record):
    return reverse("feed-detail", args=[record.id], host="data")


class DatasetTable(GovUkTable):
    pagination_top = False
    pagination_bottom = True

    name = tables.Column(
        verbose_name="Data set",
        attrs={"a": {"class": "govuk-link"}, "td": {"class": "name_cell"}},
        linkify=lambda record: reverse("feed-detail", args=[record.id], host="data"),
    )
    status = FeedStatusColumn(
        show_update_link=False,
        attrs={"td": {"class": "status_cell"}},
    )
    admin_area_names = TruncatedTextColumn(
        verbose_name="Geographical location",
        empty_values=(),
        orderable=False,
        limit=70,
        attrs={"td": {"class": "admin_area_cell"}},
    )
    num_of_lines = tables.Column(
        verbose_name="Number of Routes",
        attrs={"td": {"class": "num_of_routes_cell"}},
    )
    num_of_bus_stops = tables.Column(
        verbose_name="Number of Bus stops",
        attrs={"td": {"class": "num_of_stops_cell"}},
    )
    modified = tables.Column(
        verbose_name="Last Updated",
        attrs={"td": {"class": "last_updated_cell"}},
    )

    class Meta(GovUkTable.Meta):
        fields = ("status", "name", "num_of_lines", "num_of_bus_stops", "modified")
        sequence = (
            "name",
            "status",
            "admin_area_names",
            "num_of_lines",
            "num_of_bus_stops",
            "modified",
        )
        attrs = {
            "th": {"class": "govuk-table__header"},
        }

    def render_modified(self, value):
        return format_html(
            """
                            <div>{}</div>
                            """,
            value.astimezone(pytz.timezone("Europe/London")).strftime(
                "%d %b %Y %I:%M%P"
            ),
        )


class DatasetSubscriptionTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        fields = ("status", "name", "id", "action")
        sequence = ("status", "name", "id", "action")
        attrs = {
            "caption": {"class": "govuk-heading-m"},
            "th": {"class": "govuk-table__header"},
        }

    pagination_top = False
    pagination_bottom = True
    caption = "Data sets"

    status = FeedStatusColumn(
        show_update_link=False, attrs={"td": {"class": "status_cell"}}
    )
    name = tables.Column(
        verbose_name="Data set",
        attrs={
            "a": {"class": "govuk-link"},
            "th": {"class": "govuk-table__header", "width": "40%"},
        },
        linkify=lambda record: reverse("feed-detail", args=[record.id], host="data")
        if record.dataset_type == DatasetType.TIMETABLE.value
        else reverse("avl-feed-detail", args=[record.id], host="data")
        if record.dataset_type == DatasetType.AVL.value
        else reverse("fares-feed-detail", args=[record.id], host="data"),
    )

    id = tables.Column(
        verbose_name="Data set ID",
        attrs={
            "a": {"class": "govuk-link"},
            "th": {"class": "govuk-table__header", "width": "20%"},
        },
        linkify=lambda record: reverse("feed-detail", args=[record.id], host="data")
        if record.dataset_type == DatasetType.TIMETABLE.value
        else reverse("avl-feed-detail", args=[record.id], host="data")
        if record.dataset_type == DatasetType.AVL.value
        else reverse("fares-feed-detail", args=[record.id], host="data"),
    )

    action = tables.Column(
        attrs={
            "a": {"class": "govuk-link"},
            "th": {"class": "govuk-table__header", "width": "20%"},
        },
        empty_values=(),
        orderable=False,
        linkify=lambda record: reverse(
            "feed-subscription", args=[record.id], host="data"
        )
        if record.dataset_type == DatasetType.TIMETABLE.value
        else reverse("avl-feed-subscription", args=[record.id], host="data")
        if record.dataset_type == DatasetType.AVL.value
        else reverse("fares-feed-subscription", args=[record.id], host="data"),
    )  # subscribe/unsubscribe not yet implemented for AVL

    def render_action(self, value):
        return "Unsubscribe"


class DatasetPaginatorTable:
    """When 'unsubscribe' event is triggered this delete the row in the
    Dataset, but the `back_url` has not been updated, this could
    cause an 404 error.

    BUG: https://itoworld.atlassian.net/browse/BODP-5498

    Update the number of page, according with the Dataset, using the
    class Paginator.

    """

    def _get_paginator(self, user: LazyObject) -> Paginator:
        datasets = Dataset.objects.filter(subscribers=user).add_live_data()
        return Paginator(datasets, DATASET_MANAGE_TABLE_PAGINATE_BY)

    def _get_or_update_url(self, user: LazyObject, url: str = "") -> str:
        sub_manage_url = reverse("users:feeds-manage", host=config.hosts.DATA_HOST)
        if sub_manage_url in url:
            paginator = self._get_paginator(user)
            return (
                reverse("users:feeds-manage", host=config.hosts.DATA_HOST)
                + f"?page={paginator.num_pages}&"
            )
        return url
