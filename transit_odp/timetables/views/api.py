from django.contrib.auth import get_user
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django_hosts import reverse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from waffle import flag_is_active

import config.hosts
from transit_odp.publish.forms import FeedDescriptionForm, FeedUploadForm
from transit_odp.timetables.tasks import task_dataset_pipeline
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.publish.views.trigger_state_machine import trigger_state_machine


_jwt_auth = JWTAuthentication()
FIRST_PUBLICATION_COMMENT = "First publication"
LOADING_STATUSES = {"indexing", "processing", "pending"}
AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ACCESS_REQUIRED_ERROR = "Org user access required"
ORG_NOT_FOUND_ERROR = "Organisation not found"
REVISION_NOT_FOUND_ERROR = "Dataset revision not found"


def _authenticate_jwt(request):
    """Return the authenticated user from a Bearer token, or None."""
    try:
        result = _jwt_auth.authenticate(request)
    except (InvalidToken, TokenError):
        return None
    if result is None:
        return None
    user, _token = result
    return user


def _authenticate_user(request):
    """Prefer Django session auth, then fall back to JWT."""
    session_user = get_user(request)
    if session_user is not None and session_user.is_authenticated:
        return session_user

    if (
        hasattr(request, "user")
        and request.user is not None
        and request.user.is_authenticated
    ):
        return request.user

    return _authenticate_jwt(request)


def _get_user_org(user, org_id):
    try:
        return user.organisations.get(id=org_id)
    except Organisation.DoesNotExist:
        return None


def _get_revision_for_dataset(org_id, dataset_id):
    return (
        DatasetRevision.objects.filter(
            dataset_id=dataset_id,
            dataset__organisation_id=org_id,
            is_published=False,
        )
        .order_by("-id")
        .first()
    )


def _upsert_draft_revision(dataset: Dataset, all_data: dict) -> DatasetRevision:
    return DatasetRevision.objects.filter(
        Q(dataset=dataset) & Q(is_published=False)
    ).update_or_create(dataset=dataset, is_published=False, defaults=all_data)[0]


def _trigger_timetables_processing(revision: DatasetRevision) -> None:
    is_serverless_publishing_active = flag_is_active(
        "", "is_serverless_publishing_active"
    )

    if not is_serverless_publishing_active:
        if revision.status != FeedStatus.pending.value:
            revision.to_pending()
            revision.save()

        transaction.on_commit(lambda: task_dataset_pipeline.delay(revision.id))
    else:
        trigger_state_machine(revision, "timetables")


def _get_revision_progress(revision: DatasetRevision):
    progress = 0
    latest_task = revision.etl_results.order_by("-id").first()
    error_code = None

    if latest_task is not None:
        progress = latest_task.progress or 0
        error_code = latest_task.error_code
        if error_code:
            progress = 100

    return progress, error_code


def _is_loading_status(status: str) -> bool:
    return status in LOADING_STATUSES


def _iso_or_none(value):
    if value is None:
        return None
    return value.isoformat()


def _get_request_context(request, org_id, dataset_id=None):
    user = _authenticate_user(request)
    if user is None or not user.is_authenticated:
        return (
            None,
            None,
            None,
            JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401),
        )

    if not user.is_org_user:
        return (
            None,
            None,
            None,
            JsonResponse(
                {"error": ORG_ACCESS_REQUIRED_ERROR},
                status=403,
            ),
        )

    organisation = _get_user_org(user, org_id)
    if organisation is None:
        return (
            None,
            None,
            None,
            JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404),
        )

    revision = None
    if dataset_id is not None:
        revision = _get_revision_for_dataset(org_id, dataset_id)
        if revision is None:
            return (
                None,
                None,
                None,
                JsonResponse(
                    {"error": REVISION_NOT_FOUND_ERROR},
                    status=404,
                ),
            )

    return user, organisation, revision, None


@csrf_exempt
@require_POST
def create_timetables_dataset_api(request, pk1):
    user, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return error_response

    description_form = FeedDescriptionForm(data=request.POST)
    if not description_form.is_valid():
        return JsonResponse(
            {
                "error": "Description validation failed",
                "field_errors": description_form.errors,
            },
            status=400,
        )

    upload_form = FeedUploadForm(data=request.POST, files=request.FILES)
    if not upload_form.is_valid():
        return JsonResponse(
            {
                "error": "Upload validation failed",
                "field_errors": upload_form.errors,
            },
            status=400,
        )

    all_data = {}
    all_data.update(description_form.cleaned_data)
    all_data.update(upload_form.cleaned_data)
    all_data["last_modified_user"] = user
    all_data["comment"] = FIRST_PUBLICATION_COMMENT

    with transaction.atomic():
        dataset = Dataset.objects.create(
            contact=user,
            organisation_id=organisation.id,
            dataset_type=DatasetType.TIMETABLE.value,
        )

        revision = _upsert_draft_revision(dataset, all_data)
        _trigger_timetables_processing(revision)

    review_url = f"/publish/org/{organisation.id}/dataset/timetable/{dataset.id}/review"

    return JsonResponse({"redirect": review_url}, status=201)


@csrf_exempt
@require_GET
def get_timetables_review_status_api(request, pk1, pk):
    _, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    progress, error_code = _get_revision_progress(revision)

    status = revision.status
    is_loading = _is_loading_status(status)

    txc_attributes = revision.txc_file_attributes.all()
    metadata = [
        {
            "filename": attr.filename,
            "serviceCode": attr.service_code,
            "nationalOperatorCode": attr.national_operator_code,
            "lineNames": attr.line_names,
            "origin": attr.origin,
            "destination": attr.destination,
            "operatingPeriodStartDate": _iso_or_none(attr.operating_period_start_date),
            "operatingPeriodEndDate": _iso_or_none(attr.operating_period_end_date),
            "schemaVersion": attr.schema_version,
            "revisionNumber": attr.revision_number,
            "modification": attr.modification,
            "serviceMode": attr.service_mode,
        }
        for attr in txc_attributes
    ]

    download_url = revision.url_link
    if not download_url:
        download_url = (
            reverse(
                "feed-download",
                kwargs={"pk1": pk1, "pk": pk},
                host=config.hosts.PUBLISH_HOST,
            )
            + "?is_review=true"
        )

    last_modified_user = None
    if revision.last_modified_user is not None:
        last_modified_user = revision.last_modified_user.username

    return JsonResponse(
        {
            "datasetId": revision.dataset_id,
            "revisionId": revision.id,
            "status": status,
            "progress": progress,
            "loading": is_loading,
            "name": revision.name,
            "description": revision.description,
            "shortDescription": revision.short_description,
            "urlLink": revision.url_link,
            "ownerName": revision.dataset.organisation.name,
            "downloadUrl": download_url,
            "lastModified": _iso_or_none(revision.modified),
            "lastModifiedUser": last_modified_user,
            "metadata": metadata,
            "error": error_code,
        },
        status=200,
    )


@csrf_exempt
@require_POST
def publish_timetables_dataset_api(request, pk1, pk):
    user, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    if _is_loading_status(revision.status):
        return JsonResponse({"error": "Dataset is still processing"}, status=409)

    if not revision.is_published:
        revision.publish(user)

    return JsonResponse(
        {
            "redirect": f"/publish/org/{pk1}/dataset/timetable",
            "published": True,
        },
        status=200,
    )