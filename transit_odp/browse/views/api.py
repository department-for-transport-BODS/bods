"""JSON endpoints used by the Next.js data browser (data host, ``browser/...``)."""
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET
from waffle import flag_is_active

from transit_odp.browse.views.local_authority import (
    LocalAuthorityView,
    get_lta_detail_summary,
    get_lta_licence_organisation_map,
)
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.templatetags.paginator_range import paginator_range
from transit_odp.otc.models import LocalAuthority

LTA_NOT_FOUND_ERROR = "Local transport authority not found"
LTA_ORDERINGS = ("ui_lta_name_trimmed", "-ui_lta_name_trimmed")


def _parse_auth_ids(raw_auth_ids):
    """
    Parse ``auth_ids`` the way the Django detail/export views do (``1,2`` or
    ``[1, 2]``). Returns None when missing or malformed.
    """
    if not raw_auth_ids:
        return None
    try:
        return [
            int(lta_id.replace("[", "").replace("]", ""))
            for lta_id in raw_auth_ids.split(",")
        ]
    except ValueError:
        return None


@require_GET
def local_authority_list_api(request):
    """Data ``local-authority`` list page. Public, like the Django page."""
    ordering = request.GET.get("ordering", "ui_lta_name_trimmed")
    if ordering not in LTA_ORDERINGS:
        return JsonResponse({"error": "Invalid ordering."}, status=400)

    # Reuse the Django view for search, ordering, paging and the per-LTA
    # compliance numbers so both frontends always agree.
    view = LocalAuthorityView(request=request, kwargs={})
    view.object_list = view.get_queryset()
    try:
        context = view.get_context_data()
    except Http404:
        return JsonResponse({"error": "Invalid page."}, status=404)

    page = context["page_obj"]
    return JsonResponse(
        {
            "results": [
                {
                    "name": lta.ui_lta_name(),
                    "authIds": lta.auth_ids,
                    "servicesRequireAttentionPercentage": (
                        lta.services_require_attention_percentage
                    ),
                }
                for lta in context["object_list"]
            ],
            "count": context["updated_result"],
            "page": page.number,
            "numPages": page.paginator.num_pages,
            "pageRange": list(paginator_range(page, page.paginator)),
            "pageSize": page.paginator.per_page,
            "q": context["q"],
            "ordering": ordering,
            "names": context["ltas"]["names"],
        }
    )


def _licence_payload(licence):
    org_id = licence.get("licence_organisation_id")
    return {
        "licenceNumber": licence["licence_number"],
        "operatorName": licence["operator_name"],
        "licenceOrganisationId": (
            None if org_id is None or org_id != org_id else int(org_id)
        ),
        "nonCompliant": bool(licence.get("non_compliant")),
    }


@require_GET
def local_authority_detail_api(request):
    """Data ``local-authority-detail`` page. Public, like the Django page."""
    raw_auth_ids = request.GET.get("auth_ids")
    auth_ids = _parse_auth_ids(raw_auth_ids)
    if not auth_ids:
        return JsonResponse({"error": LTA_NOT_FOUND_ERROR}, status=404)

    lta_objs = []
    for auth_id in auth_ids:
        try:
            lta_objs.append(LocalAuthority.objects.get(id=auth_id))
        except ObjectDoesNotExist:
            return JsonResponse({"error": LTA_NOT_FOUND_ERROR}, status=404)

    is_avl_active = flag_is_active("", FeatureFlags.AVL_REQUIRES_ATTENTION.value)
    is_fares_active = flag_is_active("", FeatureFlags.FARES_REQUIRE_ATTENTION.value)
    is_complete_active = flag_is_active("", FeatureFlags.COMPLETE_SERVICE_PAGES.value)
    is_prefetch_active = flag_is_active("", FeatureFlags.UILTA_PREFETCH_SRA.value)

    summary = get_lta_detail_summary(
        lta_objs, is_avl_active, is_fares_active, is_prefetch_active
    )
    try:
        percentage = round(100 * (summary["timetable_sra"] / summary["total_inscope"]))
    except ZeroDivisionError:
        percentage = 0

    payload = {
        "name": lta_objs[0].ui_lta_name(),
        "authIds": raw_auth_ids,
        "isCompleteServicePagesActive": is_complete_active,
        "isAvlRequireAttentionActive": is_avl_active,
        "isFaresRequireAttentionActive": is_fares_active,
        "totalInScopeInSeasonServices": summary["total_inscope"],
        "servicesRequireAttentionPercentage": percentage,
        "totalTimetableRecordsRequiringAttention": summary["timetable_sra"],
        "totalServicesRequiringAttention": None,
        "totalLocationRecordsRequiringAttention": None,
        "totalFaresRecordsRequiringAttention": None,
        "licences": [],
    }
    if is_complete_active:
        payload.update(
            {
                "totalServicesRequiringAttention": summary["overall_sra"],
                "totalLocationRecordsRequiringAttention": summary["avl_sra"],
                "totalFaresRecordsRequiringAttention": summary["fares_sra"],
                "licences": [
                    _licence_payload(licence)
                    for licence in get_lta_licence_organisation_map(lta_objs)
                ],
            }
        )
    return JsonResponse(payload)
