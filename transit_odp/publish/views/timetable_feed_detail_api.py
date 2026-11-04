"""JSON APIs backing the Next.js publish timetable feed detail pages.

``get_timetables_feed_detail_api`` mirrors ``FeedDetailView`` (``feed-detail``)
and ``get_timetables_feed_line_detail_api`` mirrors ``LineMetadataDetailView``
(``line-detail``). Both are scoped to the organisation's published (live)
revision, as the Django pages are.
"""

from django.http import JsonResponse
from django.utils import formats, timezone
from django.views.decorators.http import require_GET

from transit_odp.common.templatetags.filters import percentage
from transit_odp.publish.views.timetable.detail import (
    FeedDetailView,
    LineMetadataDetailView,
)
from transit_odp.timetables.views.api import (
    AUTH_REQUIRED_ERROR,
    ORG_ACCESS_REQUIRED_ERROR,
    _authenticate_user,
    _serialise_txc_attributes,
)
from transit_odp.timetables.views.line_detail_api import (
    build_publish_line_detail_payload,
)
from transit_odp.users.constants import AccountType

DATASET_NOT_FOUND_ERROR = "Dataset not found"
PUBLISHED_AT_FORMAT = "j M Y H:i"


def _get_feed_dataset(request, pk1, pk, view_class):
    """Authorise like ``OrgUserViewMixin`` and load the published dataset.

    Returns ``(organisation, dataset, view, error_response)``.
    """
    user = _authenticate_user(request)
    if user is None:
        return (
            None,
            None,
            None,
            JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401),
        )

    organisation = user.organisations.filter(id=pk1).first()
    if (
        not user.is_org_user
        or user.account_type == AccountType.abods_user.value
        or organisation is None
    ):
        return (
            None,
            None,
            None,
            JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403),
        )

    view = view_class()
    view.setup(request, pk1=pk1, pk=pk)
    dataset = view.get_queryset().filter(pk=pk).first()
    if dataset is None:
        return (
            None,
            None,
            None,
            JsonResponse({"error": DATASET_NOT_FOUND_ERROR}, status=404),
        )
    return organisation, dataset, view, None


def _published_at(dataset) -> dict:
    published_at = dataset.published_at
    if published_at is None:
        return {"publishedAt": None, "publishedAtDisplay": ""}
    return {
        "publishedAt": published_at.isoformat(),
        "publishedAtDisplay": formats.date_format(
            timezone.localtime(published_at), PUBLISHED_AT_FORMAT
        ),
    }


def _serialize_data_quality(context) -> dict:
    """The ``snippets/data_quality_row.html`` inputs for the live revision."""
    report_id = context["report_id"]
    if context["new_dqs_report"]:
        critical = context["warning_data"].data.get("Critical", {}).get("count", 0)
        return {
            "reportId": report_id,
            "isNewService": True,
            "hasCriticalIssues": int(critical) > 0,
            "rag": None,
        }

    rag = context["dq_score"]
    return {
        "reportId": report_id,
        "isNewService": False,
        "hasCriticalIssues": None,
        "rag": {
            "score": percentage(rag.score, 0),
            "ragLevel": rag.rag_level,
            "cssIndicator": rag.css_indicator,
        }
        if rag
        else None,
    }


@require_GET
def get_timetables_feed_detail_api(request, pk1, pk):
    """Publish ``feed-detail`` page data."""
    organisation, dataset, view, error_response = _get_feed_dataset(
        request, pk1, pk, FeedDetailView
    )
    if error_response is not None:
        return error_response

    view.object = dataset
    context = view.get_context_data()
    live_revision = dataset.live_revision
    published_by = live_revision.published_by

    return JsonResponse(
        {
            "orgId": organisation.id,
            "datasetId": dataset.id,
            "liveRevisionId": live_revision.id,
            "name": dataset.name,
            "description": dataset.description,
            "shortDescription": dataset.short_description,
            "ownerName": organisation.name,
            "urlLink": dataset.url_link or None,
            "transxchangeVersion": (
                str(dataset.transxchange_version)
                if dataset.transxchange_version is not None
                else None
            ),
            # "success" or "error": picks the Django template branch.
            "status": context["status"],
            "datasetStatus": dataset.status,
            **_published_at(dataset),
            "publishedBy": published_by.username if published_by else None,
            "severeErrors": [error.description for error in context["severe_errors"]],
            "dataQuality": _serialize_data_quality(context),
            "showPti": context["show_pti"],
            "hasPtiViolations": bool(
                context["is_schema_violation"]
                or context["is_post_schema_violation"]
                or context["is_pti_violation"]
            ),
            "distinctAttributes": _serialise_txc_attributes(
                context["distinct_attributes"]
            ),
        }
    )


@require_GET
def get_timetables_feed_line_detail_api(request, pk1, pk):
    """Publish ``line-detail`` page data (live revision of the dataset)."""
    organisation, dataset, _, error_response = _get_feed_dataset(
        request, pk1, pk, LineMetadataDetailView
    )
    if error_response is not None:
        return error_response

    return JsonResponse(
        build_publish_line_detail_payload(request, organisation, dataset.live_revision)
    )
