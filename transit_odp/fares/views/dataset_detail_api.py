"""JSON API backing the Next.js fares dataset detail page.

Data host: mirrors browse ``FaresDatasetDetailView`` (``fares-feed-detail``).
The page is public, so there is no login check here. The queryset, visibility
rules and context come straight from the Django view so both frontends agree
on which datasets can be seen and what is shown for them.

Next.js owns the feature flags it renders with (``is_fares_validator_active``),
so this payload carries the raw compliance facts the template branches on.
"""

from django.http import JsonResponse
from django.template import Context
from django.template.base import render_value_in_context
from django.views.decorators.http import require_GET

from transit_odp.browse.views.fares_views import FaresDatasetDetailView
from transit_odp.timetables.views.dataset_detail_api import (
    DATASET_NOT_FOUND_ERROR,
    format_last_updated,
)


def _display(value) -> str:
    """The string Django's template engine prints for ``{{ value }}``.

    Metadata values (counts, validity dates) are shown exactly as the template
    shows them, including localised dates and a literal "None" when empty.
    """
    return render_value_in_context(value, Context(autoescape=False))


def _serialize_metadata(metadata) -> dict:
    return {
        "schemaVersion": _display(metadata.schema_version),
        "numOfFareZones": _display(metadata.num_of_fare_zones),
        "numOfLines": _display(metadata.num_of_lines),
        "numOfSalesOfferPackages": _display(metadata.num_of_sales_offer_packages),
        "numOfFareProducts": _display(metadata.num_of_fare_products),
        "numOfUserProfiles": _display(metadata.num_of_user_profiles),
        "validFrom": _display(metadata.valid_from),
        "validTo": _display(metadata.valid_to),
    }


@require_GET
def get_browse_fares_detail_api(request, pk):
    """Data ``fares-feed-detail`` page data. Public, like the Django page."""
    detail_view = FaresDatasetDetailView(request=request, kwargs={"pk": pk})
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
            "lastUpdated": format_last_updated(dataset.published_at),
            "publishedBy": published_by.username if published_by else None,
            "showMap": context["show_map"],
            "isCompliantError": context["is_compliant_error"],
            "showReportLink": context["show_report_link"],
            "metadata": _serialize_metadata(context["metadata"]),
            "isSubscribed": bool(context["notification"]),
            "feedApi": context["feed_api"],
        }
    )
