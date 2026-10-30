"""JSON API backing the Next.js timetable dataset detail page.

Data host: mirrors browse ``DatasetDetailView`` (``feed-detail``). The page is
public, so there is no login check here. The queryset, visibility rules and
context are taken straight from the Django view so both frontends agree on
which datasets can be seen and what is shown for them.

Next.js owns the feature flags it renders with (``is_specific_feedback``), so
this payload carries the raw facts the template branches on.
"""

from typing import Dict, List, Optional

from django.http import JsonResponse
from django.utils import dateformat, timezone
from django.views.decorators.http import require_GET

from transit_odp.browse.views.timetable_views import DatasetDetailView
from transit_odp.common.templatetags.filters import percentage

DATASET_NOT_FOUND_ERROR = "Dataset not found"
LAST_UPDATED_FORMAT = "j M Y H:i"


def _format_published_at(published_at) -> Optional[str]:
    """Same output as the template's ``published_at|date:"j M Y H:i"``."""
    if not published_at:
        return None
    return dateformat.format(timezone.localtime(published_at), LAST_UPDATED_FORMAT)


def _serialize_service_numbers(distinct_attributes: Dict) -> List[dict]:
    """Licence number -> NOC -> line name -> service codes, as ordered lists."""
    return [
        {
            "licenceNumber": licence_number,
            "nocs": [
                {
                    "noc": noc,
                    "lines": [
                        {
                            "lineName": line_name,
                            "serviceCodes": sorted(service_codes),
                        }
                        for line_name, service_codes in lines.items()
                    ],
                }
                for noc, lines in nocs.items()
            ],
        }
        for licence_number, nocs in distinct_attributes.items()
    ]


def _count(level_data: Optional[dict]):
    """``level_data["count"]``, or None when the level is missing."""
    if not isinstance(level_data, dict):
        return None
    count = level_data.get("count")
    return None if count is None else int(count)


def _serialize_data_quality(context: dict) -> Optional[dict]:
    """The data quality row, or None when the template would not render it."""
    if context["new_dqs_report"]:
        data = getattr(context["summary"], "data", None) or {}
        return {
            "newDqsReport": True,
            "reportId": context["report_id"],
            "criticalCount": _count(data.get("Critical")),
            "feedbackCount": _count(data.get("Feedback")),
            "score": None,
            "cssIndicator": None,
            "ragLevel": None,
        }

    dq_score = context["dq_score"]
    if dq_score is None:
        return None
    return {
        "newDqsReport": False,
        "reportId": context["report_id"],
        "criticalCount": None,
        "feedbackCount": None,
        "score": percentage(dq_score.score, 0),
        "cssIndicator": dq_score.css_indicator,
        "ragLevel": str(dq_score.rag_level).upper(),
    }


@require_GET
def get_browse_timetable_detail_api(request, pk):
    """Data ``feed-detail`` page data. Public, like the Django page."""
    detail_view = DatasetDetailView(request=request, kwargs={"pk": pk})
    dataset = detail_view.get_queryset().filter(id=pk).first()
    if dataset is None:
        return JsonResponse({"error": DATASET_NOT_FOUND_ERROR}, status=404)

    detail_view.object = dataset
    context = detail_view.get_context_data()
    live_revision = dataset.live_revision
    published_by = live_revision.published_by

    return JsonResponse(
        {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "organisationId": dataset.organisation_id,
            "organisationName": dataset.organisation.name,
            "status": dataset.status,
            "revisionId": live_revision.id,
            "transxchangeVersion": dataset.transxchange_version,
            "uploadFileExtension": live_revision.upload_file_extension,
            "lastUpdated": _format_published_at(dataset.published_at),
            "publishedBy": published_by.username if published_by else None,
            "error": context["error"],
            "dataQuality": _serialize_data_quality(context),
            "isSubscribed": bool(context["notification"]),
            "feedApi": context["feed_api"],
            "serviceNumbers": _serialize_service_numbers(
                context["distinct_attributes"]
            ),
        }
    )
