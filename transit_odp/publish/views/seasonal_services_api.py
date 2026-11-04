"""JSON endpoints used by the Next.js seasonal services journey.

These mirror ``transit_odp.publish.views.timetable.seasonal_services`` (the
Django HTML views) and reuse the same forms, querysets and pagination.
"""

import json

from django.contrib.auth import get_user
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django_tables2.paginators import Paginator

from transit_odp.organisation.models import SeasonalService
from transit_odp.publish.forms.seasonal_services import (
    DeleteForm,
    EditDateForm,
    EditRegistrationCodeDateForm,
    LicenceNumberForm,
)
from transit_odp.users.constants import DATASET_MANAGE_TABLE_PAGINATE_BY, AccountType

AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ACCESS_REQUIRED_ERROR = "Org user access required"
SEASONAL_SERVICE_NOT_FOUND_ERROR = "Seasonal service not found"

DEFAULT_SORT = "service_ends"
SORT_FIELDS = {
    "licence_number": "licence__number",
    "service_code": "registration_number",
    "service_begins": "start",
    "service_ends": "end",
}


def _json_body(request) -> dict:
    if not request.body:
        return {}
    try:
        body = json.loads(request.body)
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _camel_case(field: str) -> str:
    head, *rest = field.split("_")
    return head + "".join(part.title() for part in rest)


def _form_field_errors(form) -> dict:
    errors = {}
    for field, messages in form.errors.items():
        key = "form" if field == "__all__" else _camel_case(field)
        errors[key] = [str(message) for message in messages]
    return errors


def _validation_response(form, message="Validation failed"):
    return JsonResponse(
        {"error": message, "field_errors": _form_field_errors(form)}, status=400
    )


def _get_org_context(request, org_id):
    """Mirror ``OrgUserViewMixin``: org users who belong to the organisation."""
    user = get_user(request)
    if user is None or not user.is_authenticated:
        return None, None, JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    forbidden = JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)
    if user.account_type == AccountType.abods_user.value or not user.is_org_user:
        return None, None, forbidden

    organisation = user.organisations.filter(id=org_id).first()
    if organisation is None:
        return None, None, forbidden

    return user, organisation, None


def _organisation_payload(user, organisation) -> dict:
    return {
        "organisationId": organisation.id,
        "organisationName": organisation.name,
        "isAgentUser": user.is_agent_user,
    }


def _serialise_seasonal_service(service) -> dict:
    licence_number = service.licence.number
    return {
        "id": service.id,
        "licenceNumber": licence_number,
        "registrationCode": service.registration_code,
        "serviceCode": f"{licence_number}/{service.registration_code}",
        "start": service.start.isoformat(),
        "end": service.end.isoformat(),
        "serviceBegins": service.start.strftime("%d/%m/%Y"),
        "serviceEnds": service.end.strftime("%d/%m/%Y"),
    }


def _get_page_param(value):
    return None if value in (None, "") else str(value)


@require_GET
def list_seasonal_services_api(request, pk1):
    user, organisation, error = _get_org_context(request, pk1)
    if error is not None:
        return error

    sort_param = request.GET.get("sort", DEFAULT_SORT)
    descending = sort_param.startswith("-")
    sort_key = sort_param.lstrip("-")
    if sort_key not in SORT_FIELDS:
        sort_key, descending = DEFAULT_SORT, False
    order_field = SORT_FIELDS[sort_key]

    queryset = (
        SeasonalService.objects.filter(licence__organisation_id=organisation.id)
        .add_registration_number()
        .select_related("licence")
        .order_by(f"-{order_field}" if descending else order_field, "id")
    )
    paginator = Paginator(queryset, DATASET_MANAGE_TABLE_PAGINATE_BY)
    page_obj = paginator.get_page(request.GET.get("page"))

    return JsonResponse(
        {
            **_organisation_payload(user, organisation),
            "counter": SeasonalService.objects.get_count_in_organisation(
                organisation.id
            ),
            "results": [_serialise_seasonal_service(s) for s in page_obj.object_list],
            "sort": f"-{sort_key}" if descending else sort_key,
            "pagination": {
                "page": page_obj.number,
                "totalPages": paginator.num_pages,
                "count": paginator.count,
                "pageSize": DATASET_MANAGE_TABLE_PAGINATE_BY,
            },
        }
    )


@require_GET
def get_seasonal_service_licences_api(request, pk1):
    user, organisation, error = _get_org_context(request, pk1)
    if error is not None:
        return error

    form = LicenceNumberForm(org_id=organisation.id)
    return JsonResponse(
        {
            **_organisation_payload(user, organisation),
            "licences": [
                {"id": licence.id, "number": licence.number}
                for licence in form.fields["licence"].queryset.order_by("id")
            ],
        }
    )


@require_POST
def validate_seasonal_service_licence_api(request, pk1):
    """Wizard step 1: validate the selected PSV licence number."""
    user, organisation, error = _get_org_context(request, pk1)
    if error is not None:
        return error

    body = _json_body(request)
    form = LicenceNumberForm(
        data={"licence": body.get("licence")}, org_id=organisation.id
    )
    if not form.is_valid():
        return _validation_response(form)

    licence = form.cleaned_data["licence"]
    return JsonResponse({"licence": {"id": licence.id, "number": licence.number}})


@require_POST
def create_seasonal_service_api(request, pk1):
    """Wizard step 2: re-validate both steps and create the seasonal service."""
    user, organisation, error = _get_org_context(request, pk1)
    if error is not None:
        return error

    body = _json_body(request)
    licence_form = LicenceNumberForm(
        data={"licence": body.get("licence")}, org_id=organisation.id
    )
    if not licence_form.is_valid():
        return _validation_response(licence_form)

    licence = licence_form.cleaned_data["licence"]
    form = EditRegistrationCodeDateForm(
        data={
            "registration_code": body.get("registrationCode"),
            "start": body.get("start"),
            "end": body.get("end"),
        },
        licence=licence,
        org_id=organisation.id,
    )
    if not form.is_valid():
        return _validation_response(form)

    with transaction.atomic():
        service = SeasonalService.objects.create(
            licence=licence,
            registration_code=form.cleaned_data["registration_code"],
            start=form.cleaned_data["start"],
            end=form.cleaned_data["end"],
        )
    return JsonResponse({"id": service.id}, status=201)


def _get_seasonal_service(organisation, pk):
    return (
        SeasonalService.objects.filter(licence__organisation__id=organisation.id, id=pk)
        .select_related("licence")
        .first()
    )


@require_GET
def get_seasonal_service_api(request, pk1, pk):
    user, organisation, error = _get_org_context(request, pk1)
    if error is not None:
        return error

    service = _get_seasonal_service(organisation, pk)
    if service is None:
        return JsonResponse({"error": SEASONAL_SERVICE_NOT_FOUND_ERROR}, status=404)

    return JsonResponse(
        {
            **_organisation_payload(user, organisation),
            **_serialise_seasonal_service(service),
        }
    )


@require_POST
def update_seasonal_service_dates_api(request, pk1, pk):
    user, organisation, error = _get_org_context(request, pk1)
    if error is not None:
        return error

    service = _get_seasonal_service(organisation, pk)
    if service is None:
        return JsonResponse({"error": SEASONAL_SERVICE_NOT_FOUND_ERROR}, status=404)

    body = _json_body(request)
    form = EditDateForm(
        data={"start": body.get("start"), "end": body.get("end")},
        instance=service,
        org_id=organisation.id,
    )
    if not form.is_valid():
        return _validation_response(form)

    with transaction.atomic():
        service.start = form.cleaned_data["start"]
        service.end = form.cleaned_data["end"]
        service.save()
    return JsonResponse({"id": service.id})


@require_POST
def delete_seasonal_service_api(request, pk1):
    user, organisation, error = _get_org_context(request, pk1)
    if error is not None:
        return error

    body = _json_body(request)
    form = DeleteForm(data={"id": body.get("id")}, org_id=organisation.id)
    if not form.is_valid():
        return _validation_response(form)

    form.save()

    # Same page clamping as the Django ``DeleteView.get_success_url``.
    remaining = SeasonalService.objects.filter(
        licence__organisation__id=organisation.id
    ).order_by("end")
    page_obj = Paginator(remaining, DATASET_MANAGE_TABLE_PAGINATE_BY).get_page(
        _get_page_param(body.get("page"))
    )
    return JsonResponse({"deleted": True, "page": page_obj.number})
