"""JSON APIs backing the Next.js operator profile pages (data host).

Mirrors ``OperatorsView``, ``OperatorDetailView``, ``ContactOperatorView``,
``LicenceDetailView`` and ``LicenceLineMetadataDetailView`` in ``operators.py`` /
``contact_operator.py``. The list shares its queryset helper
with the HTML view and the detail endpoint runs ``OperatorDetailView``'s own
``get_context_data`` so the compliance numbers cannot drift between frontends.

Django resolves the waffle flags that shape these pages and returns them in the
payload, so Next.js renders exactly the branch Django would have rendered.
"""

import json
from typing import Optional

import pandas as pd
from django.core.paginator import EmptyPage, Paginator
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import floatformat
from django.utils import formats
from django.utils.timezone import template_localtime
from django.views.decorators.http import require_GET, require_http_methods

from transit_odp.browse.forms import ConsumerFeedbackForm
from transit_odp.browse.views.contact_operator import (
    send_operator_feedback_notifications,
)
from transit_odp.browse.views.operators import (
    LicenceDetailView,
    LicenceLineMetadataDetailView,
    OperatorDetailView,
    get_active_operators_queryset,
)
from transit_odp.common.templatetags.paginator_range import paginator_range
from transit_odp.organisation.models import Organisation
from transit_odp.otc.models import Licence as OTCLicence
from transit_odp.timetables.views.line_detail_api import (
    _serialize_booking,
    _serialize_direction,
)

OPERATORS_PAGE_SIZE = 10
DEFAULT_ORDERING = "name"
ORDERING_FIELDS = {"name", "-name", "created", "-created"}

AUTH_REQUIRED_ERROR = "Authentication required"
ORGANISATION_NOT_FOUND_ERROR = "Operator not found"
LICENCE_NOT_FOUND_ERROR = "Licence not found"
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


def _optional_int(value) -> Optional[int]:
    return None if value is None or pd.isna(value) else int(value)


def _render_date(value) -> Optional[str]:
    """A date as ``{{ value }}`` prints it in a template (localised, tz-converted)."""
    if value is None or pd.isnull(value):
        return None
    return formats.localize(template_localtime(value))


def _serialize_files(files) -> list:
    return [
        {
            "filename": file["filename"],
            "startDate": _render_date(file["start_date"]),
            "endDate": _render_date(file["end_date"]),
        }
        for file in files or []
    ]


def _serialize_licence_service(service: dict) -> dict:
    """One row of ``licence_services`` (prefetched compliance report or legacy map)."""
    return {
        "serviceNumber": service.get("service_number"),
        "registrationNumber": service.get("registration_number"),
        "fullRegistrationNumber": service.get("full_registration_number"),
        "licenceOrganisationId": _optional_int(service.get("licence_organisation_id")),
        # Comma separated UILta ids, matching the template's data-local-authority.
        "localAuthorityIds": service.get("local_authorities_ids_strs") or "",
        "isInScope": bool(service.get("is_in_scope")),
        "isInSeason": bool(service.get("is_in_season")),
        "requiresAttention": service.get("requires_attention") == "Yes",
        "avlRequiresAttention": service.get("avl_requires_attention") == "Yes",
        "faresRequiresAttention": service.get("fares_requires_attention") == "Yes",
        "isLabelGreen": bool(service.get("is_label_green")),
        "labelStr": service.get("label_str") or "",
    }


@require_GET
def licence_detail_api(request, number):
    """GET ``/api/browser/operators/licence/<number>/`` for ``LicenceDetailView``.

    The HTML view reads ``org_id`` from the URL kwargs, which the URLconf never
    supplies, so the ``?org_id=`` in its links is ignored. The API does the same.
    """
    view = LicenceDetailView()
    view.setup(request, number=number)
    try:
        view.object = view.get_object()
    except OTCLicence.DoesNotExist:
        return JsonResponse({"error": LICENCE_NOT_FOUND_ERROR}, status=404)

    context = view.get_context_data(object=view.object)

    return JsonResponse(
        {
            "licenceNumber": context["licence_number"],
            "organisationId": context["organisation_id"],
            "organisationName": context["organisation_name"],
            "isPrefetchComplianceReportActive": bool(
                context["is_prefetch_compliance_report_active"]
            ),
            "hasFranchise": bool(context["has_frencise"]),
            "hasNullLocalAuthority": bool(context.get("has_null_local_authority")),
            "localAuthorities": [
                {"id": int(row["id"]), "name": str(row["name"])}
                for row in context.get("local_authorities_list", [])
            ],
            "franchises": [
                {
                    "id": int(row["organisation_id"]),
                    "name": str(row["organisation_name"]),
                }
                for row in context.get("frencise_list", [])
            ],
            "operators": [
                {
                    "id": int(row["licence_organisation_id"]),
                    "name": str(row["licence_organisation_name"]),
                }
                for row in context.get("organisations_list", [])
            ],
            "services": [
                _serialize_licence_service(service)
                for service in context["licence_services"]
            ],
        }
    )


def _serialize_licence_timetable(context) -> Optional[dict]:
    """The context's visualiser data, shaped like ``line_detail_api``'s payload."""
    timetable = context.get("timetable")
    if timetable is None:
        return None

    directions = []
    for direction, details in timetable.items():
        directions.append(
            _serialize_direction(
                direction,
                {
                    "stops": details["stops"],
                    "observations": details["observations"],
                    "description": details["start_and_end"],
                },
                {
                    "df_timetable": details["df"],
                    "total_page": details["total_page"],
                    "curr_page": details["curr_page"],
                    "show_all": details["show_all"],
                    "total_row_count": details["total_row_count"],
                },
            )
        )
    return {
        "currDate": context["curr_date"],
        "isTimetableInfoAvailable": bool(context["is_timetable_info_available"]),
        "directions": directions,
    }


@require_GET
def licence_line_detail_api(request, number):
    """GET ``/api/browser/operators/licence/<number>/line/details/`` for
    ``LicenceLineMetadataDetailView``.

    Takes the view's query parameters (``line``, ``service``, ``pf``, ``date``,
    ``outboundPage``...). Like the HTML view it never 404s: an unknown licence or
    service renders with "Organisation not yet created" and no data.
    """
    view = LicenceLineMetadataDetailView()
    view.setup(request, number=number)
    view.object = view.get_object()
    context = view.get_context_data(object=view.object)

    dataset = view.object
    live_revision = dataset.live_revision if dataset else None
    organisation = context["organisation"]

    booking = {"bookingArrangements": None, "bookingMethods": None}
    if context.get("booking_methods"):
        booking = _serialize_booking(
            context["service_type"],
            [(context.get("booking_arrangements"), *context["booking_methods"])],
        )

    timetable = _serialize_licence_timetable(context)
    outbound = (context.get("timetable") or {}).get("outbound") or {}

    def optional_bool(key):
        value = context.get(key)
        return None if value is None else bool(value)

    return JsonResponse(
        {
            "licenceNumber": context["licence_number"],
            "lineName": context["line_name"],
            "serviceCode": context["service_code"],
            "isLicencePage": bool(context["licence_page"]),
            "organisation": (
                {"id": organisation.id, "name": organisation.name}
                if organisation
                else None
            ),
            "datasetId": dataset.id if dataset else None,
            "revisionId": live_revision.id if live_revision else None,
            "flags": {
                "isCompleteServicePagesActive": bool(
                    context["is_complete_service_pages_active"]
                ),
                "isCompleteServicePagesRealTimeDataActive": bool(
                    context["is_complete_service_pages_real_time_data_active"]
                ),
                "isAvlRequireAttentionActive": bool(
                    context["is_avl_require_attention_active"]
                ),
                "isFaresRequireAttentionActive": bool(
                    context["is_fares_require_attention_active"]
                ),
                "isTimetableVisualiserActive": bool(
                    context["is_timetable_visualiser_active"]
                ),
                "isSpecificFeedback": bool(context["is_specific_feedback"]),
            },
            # The service_in* and is_*_compliant values are only computed when the
            # dataset has a live revision, so they are null (not false) otherwise.
            "serviceInScope": optional_bool("service_inscope"),
            "serviceInSeason": optional_bool("service_inseason"),
            "isAvlCompliant": optional_bool("is_avl_compliant"),
            "isFaresCompliant": optional_bool("is_fares_compliant"),
            "isTimetableCompliant": optional_bool("is_timetable_compliant"),
            "serviceType": context["service_type"],
            **booking,
            "fares": {
                "datasetId": context.get("fares_dataset_id"),
                "tariffBasis": [str(item) for item in context.get("fares_tariff_basis", [])],
                "products": [str(item) for item in context.get("fares_products", [])],
                "validFiles": _serialize_files(context.get("fares_valid_files")),
                "futureDatedFiles": _serialize_files(
                    context.get("fares_future_dated_files")
                ),
                "expiredFiles": _serialize_files(context.get("fares_expired_files")),
            },
            "timetableFiles": {
                # `{{ timetables_dataset_id }}` (link text); the link targets `object.id`.
                "datasetId": context.get("timetables_dataset_id"),
                "validFiles": _serialize_files(context.get("timetables_valid_files")),
                "futureDatedFiles": _serialize_files(
                    context.get("timetables_future_dated_files")
                ),
                "expiredFiles": _serialize_files(
                    context.get("timetables_expired_files")
                ),
            },
            "timetable": timetable,
            # `{{ timetable.outbound.start_and_end }}` in the passenger facing heading.
            "outboundStartAndEnd": outbound.get("start_and_end"),
            "realTime": {
                "nationalOperatorCode": context.get("national_operator_code", ""),
                "vehicleJourneyCodes": context.get("vehicle_journey_codes", ""),
            },
        }
    )
