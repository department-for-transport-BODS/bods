"""JSON APIs backing the Next.js operator profile pages (data host).

Mirrors ``OperatorsView``, ``OperatorDetailView`` and ``ContactOperatorView`` in
``operators.py`` / ``contact_operator.py``. The list shares its queryset helper
with the HTML view and the detail endpoint runs ``OperatorDetailView``'s own
``get_context_data`` so the compliance numbers cannot drift between frontends.

Django resolves the waffle flags that shape these pages and returns them in the
payload, so Next.js renders exactly the branch Django would have rendered.
"""

import json
from django.core.paginator import EmptyPage, Paginator
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import floatformat
from django.views.decorators.http import require_GET, require_http_methods

from transit_odp.browse.forms import ConsumerFeedbackForm
from transit_odp.browse.views.contact_operator import (
    send_operator_feedback_notifications,
)
from transit_odp.browse.views.operators import (
    OperatorDetailView,
    get_active_operators_queryset,
)
from transit_odp.common.templatetags.paginator_range import paginator_range
from transit_odp.organisation.models import Organisation

OPERATORS_PAGE_SIZE = 10
DEFAULT_ORDERING = "name"
ORDERING_FIELDS = {"name", "-name", "created", "-created"}

AUTH_REQUIRED_ERROR = "Authentication required"
ORGANISATION_NOT_FOUND_ERROR = "Operator not found"
INVALID_PAGE_ERROR = "Invalid page"
VALIDATION_ERROR = "Validation failed"


def _json_body(request) -> dict:
    try:
        body = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return {}
    return body if isinstance(body, dict) else {}


def _page_number(request, paginator) -> int:
    """Same semantics as Django's ``MultipleObjectMixin.paginate_queryset``."""
    page = request.GET.get("page") or 1
    if page == "last":
        return paginator.num_pages
    try:
        return int(page)
    except (TypeError, ValueError):
        raise Http404(INVALID_PAGE_ERROR)


@require_GET
def operators_list_api(request):
    """GET ``/api/browser/operators/?q=&ordering=&page=``."""
    q = request.GET.get("q", "")
    ordering = request.GET.get("ordering", DEFAULT_ORDERING)
    if ordering not in ORDERING_FIELDS:
        ordering = DEFAULT_ORDERING

    queryset = get_active_operators_queryset(q, ordering)
    paginator = Paginator(queryset, OPERATORS_PAGE_SIZE)
    try:
        page = paginator.page(_page_number(request, paginator))
    except (EmptyPage, Http404):
        return JsonResponse({"error": INVALID_PAGE_ERROR}, status=404)

    names = list(
        Organisation.objects.filter(is_active=True).values_list("name", flat=True)
    )
    return JsonResponse(
        {
            "q": q,
            "ordering": ordering,
            "count": paginator.count,
            "page": page.number,
            "numPages": paginator.num_pages,
            "pageSize": OPERATORS_PAGE_SIZE,
            "pageRange": list(paginator_range(page, paginator)),
            "results": [
                {
                    "id": operator.id,
                    "name": operator.name,
                    "created": operator.created.isoformat(),
                }
                for operator in page.object_list
            ],
            "operatorNames": names,
        }
    )


@require_GET
def operator_detail_api(request, pk):
    """GET ``/api/browser/operators/<pk>/`` for ``OperatorDetailView``."""
    view = OperatorDetailView()
    view.setup(request, pk=pk)
    try:
        view.object = view.get_object()
    except Http404:
        return JsonResponse({"error": ORGANISATION_NOT_FOUND_ERROR}, status=404)

    context = view.get_context_data(object=view.object)
    organisation = view.object

    licences = [
        {
            "licenceNumber": str(licence["licence_number"]),
            "operatorName": str(licence["operator_name"]),
            "nonCompliant": bool(licence["non_compliant"]),
        }
        for licence in context.get("operator_licences", [])
    ]
    fares_stats = context.get("fares_stats")
    overall_ppc_score = context.get("overall_ppc_score")

    return JsonResponse(
        {
            "id": organisation.id,
            "name": organisation.name,
            "shortName": organisation.short_name,
            "created": organisation.created.isoformat(),
            "licenceNumbers": list(
                organisation.licences.values_list("number", flat=True)
            ),
            "nocs": list(organisation.nocs.values_list("noc", flat=True)),
            "isAuthenticated": request.user.is_authenticated,
            "flags": {
                "isCompleteServicePagesActive": bool(
                    context.get("is_complete_service_pages_active")
                ),
                "isAvlRequireAttentionActive": bool(
                    context.get("is_avl_require_attention_active")
                ),
                "isFaresRequireAttentionActive": bool(
                    context.get("is_fares_require_attention_active")
                ),
            },
            "totalInScopeInSeasonServices": context.get(
                "total_in_scope_in_season_services"
            ),
            "totalServicesRequiringAttention": context.get(
                "total_services_requiring_attention"
            ),
            "timetableServicesRequiringAttentionCount": context.get(
                "timetable_services_requiring_attention_count"
            ),
            "avlServicesRequiringAttentionCount": context.get(
                "avl_services_requiring_attention_count"
            ),
            "faresServicesRequiringAttentionCount": context.get(
                "fares_services_requiring_attention_count"
            ),
            "servicesRequireAttentionPercentage": context.get(
                "services_require_attention_percentage"
            ),
            "avlServicesRequireAttentionPercentage": context.get(
                "avl_services_require_attention_percentage"
            ),
            "faresServicesRequireAttentionPercentage": context.get(
                "fares_total_services_requiring_attention_percentage"
            ),
            "faresStats": (
                {
                    "totalDatasetCount": fares_stats.total_dataset_count,
                    "totalFareProducts": fares_stats.total_fare_products,
                }
                if fares_stats is not None
                else None
            ),
            "faresNonCompliant": context.get("fares_non_compliant"),
            # The template renders `overall_ppc_score|floatformat:"0"` (rounds half up).
            "overallPpcScore": (
                None
                if overall_ppc_score is None
                else int(floatformat(overall_ppc_score, "0"))
            ),
            "operatorLicences": licences,
            "timetableFeedUrl": context.get("timetable_feed_url"),
            "avlFeedUrl": context.get("avl_feed_url"),
            "faresFeedUrl": context.get("fares_feed_url"),
        }
    )


@require_http_methods(["GET", "POST"])
def operator_contact_api(request, pk):
    """GET/POST ``/api/browser/operators/<pk>/contact/`` for ``ContactOperatorView``.

    The HTML view only requires a login and, unlike the detail page, accepts
    organisations that are not active.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    organisation = get_object_or_404(Organisation, id=pk)
    if request.method == "GET":
        return JsonResponse({"id": organisation.id, "name": organisation.name})

    body = _json_body(request)
    form = ConsumerFeedbackForm(
        data={
            "feedback": body.get("feedback", ""),
            "anonymous": bool(body.get("anonymous")),
        },
        initial={
            "dataset_id": None,
            "organisation_id": organisation.id,
            "consumer_id": request.user.id,
        },
    )
    if not form.is_valid():
        return JsonResponse(
            {
                "error": VALIDATION_ERROR,
                "field_errors": {
                    ("form" if field == "__all__" else field): [
                        str(message) for message in messages
                    ]
                    for field, messages in form.errors.items()
                },
            },
            status=400,
        )

    with transaction.atomic():
        feedback = form.save()
        send_operator_feedback_notifications(organisation, feedback, request.user)

    return JsonResponse({"success": True})
