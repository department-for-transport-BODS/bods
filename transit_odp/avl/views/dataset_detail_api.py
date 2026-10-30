"""JSON API backing the Next.js AVL dataset detail page.

Data host: mirrors browse ``AVLDatasetDetailView`` (``avl-feed-detail``). The
page is public, so there is no login check here. The queryset, visibility
rules and context come straight from the Django view so both frontends agree
on which feeds can be seen and what is shown for them.

Next.js owns the feature flags it renders with, so this payload carries the
raw facts the template branches on.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from transit_odp.browse.views.avl_views import AVLDatasetDetailView
from transit_odp.timetables.views.dataset_detail_api import (
    DATASET_NOT_FOUND_ERROR,
    format_last_updated,
)


def _schema_version(live_revision) -> str:
    """``live_revision.metadata.schema_version``; the template shows nothing
    when the revision has no metadata row."""
    try:
        return live_revision.metadata.schema_version
    except ObjectDoesNotExist:
        return ""


@require_GET
def get_browse_avl_detail_api(request, pk):
    """Data ``avl-feed-detail`` page data. Public, like the Django page."""
    detail_view = AVLDatasetDetailView(request=request, kwargs={"pk": pk})
    dataset = detail_view.get_queryset().filter(id=pk).first()
    if dataset is None:
        return JsonResponse({"error": DATASET_NOT_FOUND_ERROR}, status=404)

    detail_view.object = dataset
    context = detail_view.get_context_data()
    live_revision = dataset.live_revision

    return JsonResponse(
        {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "organisationId": dataset.organisation_id,
            "organisationName": dataset.organisation.name,
            "status": dataset.status,
            "revisionId": live_revision.id,
            "lastUpdated": format_last_updated(dataset.published_at),
            "lastAutomatedUpdate": format_last_updated(dataset.avl_feed_last_checked),
            "siriVmVersion": _schema_version(live_revision),
            # Weekly PPC score such as "85%"; None while the report is pending.
            "avlTimetablesMatching": context["properties"]["avl_timetables_matching"],
            "isSubscribed": bool(context["notification"]),
            "feedApi": context["feed_api"],
        }
    )
