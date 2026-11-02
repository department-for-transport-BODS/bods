from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET

from transit_odp.avl.views.api import (
    AUTH_REQUIRED_ERROR,
    ORG_ACCESS_REQUIRED_ERROR,
    _authenticate_user,
)
from transit_odp.publish.views.timetable.requires_attention import (
    RequiresAttentionView,
)
from transit_odp.users.constants import AccountType

INVALID_PAGE_ERROR = "Invalid page"


def requires_attention_json_response(request, pk1, view_class, export_route):
    """
    Build the JSON payload for a "service codes requiring attention" page by
    running the Django HTML view's own queryset, search, pagination and context
    code, so the Next.js page cannot drift from the Django one.

    ``export_route`` maps a view context to the publish host path of the CSV
    export linked from the bottom of the page.
    """
    user = _authenticate_user(request)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    # Same rule as OrgUserViewMixin.has_permission: org users (not ABODS users)
    # who belong to the organisation. Django answers 403 for any other org.
    organisation = user.organisations.filter(id=pk1).first()
    if (
        not user.is_org_user
        or user.account_type == AccountType.abods_user.value
        or organisation is None
    ):
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    view = view_class()
    view.setup(request, pk1=organisation.id)
    view.object_list = view.get_queryset()
    try:
        context = view.get_context_data()
    except Http404:
        return JsonResponse({"error": INVALID_PAGE_ERROR}, status=404)

    table = context["table"]
    rows = [
        {
            "licenceNumber": row.record["licence_number"],
            "serviceCode": row.record["service_code"],
            "lineNumber": row.record["line_number"],
        }
        for row in table.page.object_list
    ]
    # Same condition as the `{% if %}` that switches the HTML template between
    # the results table and the "no results" message.
    no_results = context["services_requiring_attention"] == 0 or not table.data

    return JsonResponse(
        {
            "ancestor": context["ancestor"],
            "summary": {
                "servicesRequiringAttention": context["services_requiring_attention"],
                "totalInScopeInSeasonServices": context[
                    "total_in_scope_in_season_services"
                ],
                "percentage": context["services_require_attention_percentage"],
            },
            "rows": rows,
            "pagination": {
                "currentPage": table.page.number,
                "totalPages": table.paginator.num_pages or 1,
            },
            "query": context["q"],
            "noResults": no_results,
            "exportPath": export_route(context, organisation.id),
        }
    )


def _timetable_export_route(context, org_id):
    export_name = (
        "compliance-report"
        if context["is_avl_require_attention_active"]
        else "service-codes"
    )
    return f"/org/{org_id}/dataset/timetable/{export_name}/"


@require_GET
def get_timetable_requires_attention_api(request, pk1):
    return requires_attention_json_response(
        request, pk1, RequiresAttentionView, _timetable_export_route
    )
