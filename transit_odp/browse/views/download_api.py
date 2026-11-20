"""JSON endpoints for the Next.js data-host "download all data" pages.

Each endpoint reuses ``get_context_data`` of the Django view that renders the
equivalent HTML page, so the data and flag handling stay identical. The Django
HTML views are untouched.
"""
from django.http import JsonResponse
from django.utils.dateformat import format as format_date
from django.views.decorators.http import require_GET

from transit_odp.browse.views.avl_views import DownloadAVLView
from transit_odp.browse.views.disruptions_views import DownloadDisruptionsView
from transit_odp.browse.views.fares_views import DownloadFaresView
from transit_odp.browse.views.timetable_views import DownloadTimetablesView
from transit_odp.common.views import CoachDownloadView

AUTH_REQUIRED_ERROR = "Authentication required"


def _unauthenticated(request):
    user = getattr(request, "user", None)
    return user is None or not user.is_authenticated


def _context(view_class, request):
    view = view_class()
    view.setup(request)
    return view.get_context_data()


def _serialize_gtfs_files(context):
    """GTFS download links, from the GTFS API (new) or the S3 bucket (old)."""
    if context["is_new_gtfs_api_active"]:
        regions = context.get("gtfs_regions")
        if not isinstance(regions, list):
            return []
        return [
            {"id": region["regionName"], "name": region["regionDisplayName"]}
            for region in regions
        ]

    return [
        {"id": file.id, "name": file.pretty_name}
        for file in context.get("gtfs_static_files") or []
    ]


@require_GET
def get_download_timetables_api(request):
    """Data ``download-timetables`` page data. Login required, like the page."""
    if _unauthenticated(request):
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    context = _context(DownloadTimetablesView, request)
    return JsonResponse(
        {
            "showBulkArchiveUrl": context["show_bulk_archive_url"],
            "regions": [
                {
                    "regionCode": region.region_code,
                    "name": str(region.pretty_name_region_code),
                    "exists": region.exists,
                }
                for region in context["show_bulk_traveline_regions"]
            ],
            "changeArchives": [
                {
                    "publishedAt": archive.published_at.isoformat(),
                    "label": format_date(archive.published_at, "l j F"),
                }
                for archive in context["change_archives"]
            ],
            "isNewGtfsApiActive": context["is_new_gtfs_api_active"],
            "gtfsFiles": _serialize_gtfs_files(context),
        }
    )


@require_GET
def get_download_avl_api(request):
    """Data ``download-avl`` page data. Login required, like the page."""
    if _unauthenticated(request):
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    context = _context(DownloadAVLView, request)
    return JsonResponse({"showBulkArchiveUrl": context["show_bulk_archive_url"]})


@require_GET
def get_download_fares_api(request):
    """Data ``download-fares`` page data. Login required, like the page."""
    if _unauthenticated(request):
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    context = _context(DownloadFaresView, request)
    return JsonResponse({"showBulkArchiveUrl": context["show_bulk_archive_url"]})


@require_GET
def get_download_disruptions_api(request):
    """Data ``download-disruptions`` page data. Login required, like the page."""
    if _unauthenticated(request):
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    context = _context(DownloadDisruptionsView, request)
    return JsonResponse(
        {
            "showBulkArchiveUrl": context["show_bulk_archive_url"],
            "isGtfsServiceAlertsLive": context["is_gtfs_service_alerts_live"],
        }
    )


@require_GET
def get_download_coach_api(request):
    """Data ``coach-download`` page data. Public, like the page."""
    context = _context(CoachDownloadView, request)
    return JsonResponse(
        {"txcFile": context["txc_file"], "atcoFile": context["atco_file"]}
    )
