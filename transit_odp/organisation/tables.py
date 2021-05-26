import config.hosts
import django_tables2 as tables
from django.db.models import Case, CharField, Value, When
from django_hosts import reverse

from transit_odp.organisation.constants import STATUS_CHOICES


class FeedStatusColumn(tables.TemplateColumn):
    template_name = "organisation/snippets/status_indicator_column.html"

    def __init__(
        self, template_name=None, show_update_link=True, app_name=None, *args, **kwargs
    ):
        if not template_name:
            template_name = self.template_name

        app_prefix = "" if app_name is None else f"{app_name}:"
        extra_context = {"show_update_link": show_update_link, "app_prefix": app_prefix}
        super().__init__(
            template_name=template_name, extra_context=extra_context, *args, **kwargs
        )

    def order(self, queryset, is_descending, status_choices=STATUS_CHOICES):
        whens = [
            When(status=db_value, then=Value(display))
            for db_value, display in status_choices
        ]
        order = "-status_display" if is_descending else "status_display"
        annotated_qs = queryset.annotate(
            status_display=Case(*whens, output_field=CharField())
        ).order_by(order)
        return (annotated_qs, True)


def get_feed_name_linkify(record, app_name=None, host_name=config.hosts.PUBLISH_HOST):
    viewname = None

    if not record.draft_revisions:
        viewname = "feed-detail"
    else:
        if not record.published_at:
            if not record.live_revision:
                viewname = "revision-publish"
            else:
                viewname = "revision-update-publish"

    if all(v is not None for v in [app_name, viewname]):
        viewname = f"{app_name}:{viewname}"

    if viewname is not None:
        return reverse(
            viewname,
            kwargs={"pk": record.id, "pk1": record.organisation_id},
            host=host_name,
        )
