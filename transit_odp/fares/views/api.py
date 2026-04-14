import logging

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
from transit_odp.fares.constants import ERROR_CODE_MAP
from transit_odp.fares.forms import FaresFeedDescriptionForm, FaresFeedUploadForm
from transit_odp.fares.tasks import task_run_fares_pipeline
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.publish.views.trigger_state_machine import trigger_state_machine
from transit_odp.timetables.tasks import delete_dataset_revision
from transit_odp.validate.errors import XMLErrorMessageRenderer


_jwt_auth = JWTAuthentication()
logger = logging.getLogger(__name__)
FIRST_PUBLICATION_COMMENT = "First publication"
LOADING_STATUSES = {"indexing", "processing", "pending"}
AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ACCESS_REQUIRED_ERROR = "Org user access required"
ORG_NOT_FOUND_ERROR = "Organisation not found"
REVISION_NOT_FOUND_ERROR = "Dataset revision not found"
ACTIVE_LIST_SECTION = "active"
DRAFT_LIST_SECTION = "draft"
ARCHIVE_LIST_SECTION = "archive"
LIST_SECTIONS = {
    ACTIVE_LIST_SECTION,
    DRAFT_LIST_SECTION,
    ARCHIVE_LIST_SECTION,
}
EXCLUDED_LIVE_STATUSES = [FeedStatus.expired.value, FeedStatus.inactive.value]


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


def _trigger_fares_processing(revision: DatasetRevision) -> None:
    is_fares_serverless_publishing_active = flag_is_active(
        "", "is_fares_serverless_publishing_active"
    )

    if not is_fares_serverless_publishing_active:
        if revision.status != FeedStatus.pending.value:
            revision.to_pending()
            revision.save()

        transaction.on_commit(lambda: task_run_fares_pipeline.delay(revision.id))
    else:
        trigger_state_machine(revision, "fares")


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


def _get_error_description(revision: DatasetRevision, error_code):
    if not error_code:
        return None

    latest_task = revision.etl_results.order_by("-id").first()
    if latest_task and latest_task.additional_info:
        renderer = XMLErrorMessageRenderer(
            latest_task.additional_info,
            error_code=latest_task.error_code,
        )
        return renderer.get_message()

    mapped_error = ERROR_CODE_MAP.get(error_code)
    if mapped_error:
        return mapped_error.get("description")

    return None


def _is_loading_status(status: str) -> bool:
    return status in LOADING_STATUSES


def _get_fares_list_section(request):
    section = request.GET.get("tab", ACTIVE_LIST_SECTION)
    if section not in LIST_SECTIONS:
        return ACTIVE_LIST_SECTION
    return section


def _get_fares_list_queryset(organisation, section):
    datasets = (
        Dataset.objects.filter(
            organisation=organisation,
            dataset_type=DatasetType.FARES.value,
        )
        .select_related("organisation")
        .select_related("live_revision")
        .order_by("id")
    )

    if section == ACTIVE_LIST_SECTION:
        return (
            datasets.add_live_data()
            .exclude(status__in=EXCLUDED_LIVE_STATUSES)
            .add_draft_revisions()
        )

    if section == DRAFT_LIST_SECTION:
        return datasets.add_draft_revisions().add_draft_revision_data(
            organisation=organisation,
            dataset_type=DatasetType.FARES.value,
        )

    return (
        datasets.add_live_data()
        .filter(status__in=EXCLUDED_LIVE_STATUSES)
        .add_draft_revisions()
    )


def _dataset_row_to_json(dataset):
    return {
        "id": dataset.id,
        "name": getattr(dataset, "name", None),
        "shortDescription": getattr(dataset, "short_description", None),
        "status": getattr(dataset, "status", None),
        "modified": _iso_or_none(getattr(dataset, "modified", None)),
    }


def _iso_or_none(value):
    if value is None:
        return None
    return value.isoformat()


def _get_request_context(request, org_id, dataset_id=None):
    user = _authenticate_jwt(request)
    if user is None or not user.is_authenticated:
        return None, None, None, JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return None, None, None, JsonResponse(
            {"error": ORG_ACCESS_REQUIRED_ERROR},
            status=403,
        )

    organisation = _get_user_org(user, org_id)
    if organisation is None:
        return None, None, None, JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    revision = None
    if dataset_id is not None:
        revision = _get_revision_for_dataset(org_id, dataset_id)
        if revision is None:
            return None, None, None, JsonResponse(
                {"error": REVISION_NOT_FOUND_ERROR},
                status=404,
            )

    return user, organisation, revision, None


@csrf_exempt
@require_POST
def create_fares_dataset_api(request, pk1):
    user, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return error_response

    description_form = FaresFeedDescriptionForm(data=request.POST)
    if not description_form.is_valid():
        return JsonResponse(
            {
                "error": "Description validation failed",
                "field_errors": description_form.errors,
            },
            status=400,
        )

    upload_form = FaresFeedUploadForm(data=request.POST, files=request.FILES)
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
            dataset_type=DatasetType.FARES.value,
        )

        revision = _upsert_draft_revision(dataset, all_data)
        _trigger_fares_processing(revision)

    review_url = reverse(
        "fares:revision-publish",
        kwargs={"pk": dataset.id, "pk1": organisation.id},
        host=config.hosts.PUBLISH_HOST,
    )

    return JsonResponse({"redirect": review_url}, status=201)


@csrf_exempt
@require_GET
def get_fares_review_status_api(request, pk1, pk):
    _, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    progress, error_code = _get_revision_progress(revision)
    error_description = _get_error_description(revision, error_code)

    status = revision.status
    is_loading = _is_loading_status(status)

    schema_version = None
    metadata = {
        "numOfFareZones": None,
        "numOfLines": None,
        "numOfSalesOfferPackages": None,
        "numOfFareProducts": None,
        "numOfUserProfiles": None,
        "validFrom": None,
        "validTo": None,
    }

    try:
        revision_metadata = revision.metadata
        schema_version = revision_metadata.schema_version
        fares_metadata = getattr(revision_metadata, "faresmetadata", None)
        if fares_metadata is not None:
            metadata = {
                "numOfFareZones": fares_metadata.num_of_fare_zones,
                "numOfLines": fares_metadata.num_of_lines,
                "numOfSalesOfferPackages": fares_metadata.num_of_sales_offer_packages,
                "numOfFareProducts": fares_metadata.num_of_fare_products,
                "numOfUserProfiles": fares_metadata.num_of_user_profiles,
                "validFrom": _iso_or_none(fares_metadata.valid_from),
                "validTo": _iso_or_none(fares_metadata.valid_to),
            }
    except DatasetRevision.metadata.RelatedObjectDoesNotExist:
        pass

    download_url = revision.url_link
    if not download_url:
        download_url = (
            reverse(
                "fares:feed-download",
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
            "schemaVersion": schema_version,
            "downloadUrl": download_url,
            "lastModified": _iso_or_none(revision.modified),
            "lastModifiedUser": last_modified_user,
            "metadata": metadata,
            "error": error_code,
            "errorDescription": error_description,
        },
        status=200,
    )


@csrf_exempt
@require_GET
def get_fares_list_api(request, pk1):
    _, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return error_response

    section = _get_fares_list_section(request)
    queryset = _get_fares_list_queryset(organisation, section)
    datasets = [_dataset_row_to_json(dataset) for dataset in queryset]

    return JsonResponse({"tab": section, "results": datasets}, status=200)


@csrf_exempt
@require_POST
def publish_fares_dataset_api(request, pk1, pk):
    user, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    if _is_loading_status(revision.status):
        return JsonResponse({"error": "Dataset is still processing"}, status=409)

    if not revision.is_published:
        try:
            revision.publish(user)
        except Exception:
            # Some post-publish side effects (for example notifications)
            # can fail after the revision has already been marked published.
            revision.refresh_from_db()
            if not revision.is_published:
                logger.exception(
                    "Failed to publish fares revision",
                    extra={"org_id": pk1, "dataset_id": pk, "revision_id": revision.id},
                )
                return JsonResponse(
                    {"error": "Unable to publish this data set right now. Please try again."},
                    status=500,
                )

            logger.exception(
                "Fares revision published but post-publish side effect failed",
                extra={"org_id": pk1, "dataset_id": pk, "revision_id": revision.id},
            )

    return JsonResponse(
        {
            "redirect": f"/publish/org/{pk1}/dataset/fares/{pk}/publish-success",
            "published": True,
        },
        status=200,
    )


@csrf_exempt
@require_POST
def delete_fares_dataset_api(request, pk1, pk):
    _, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    if revision.is_published and revision.status != FeedStatus.expired.value:
        return JsonResponse(
            {
                "error": "Only draft or expired fares datasets can be deleted from this flow"
            },
            status=400,
        )

    delete_dataset_revision.delay(revision.id)

    return JsonResponse(
        {
            "redirect": f"/publish/org/{pk1}/dataset/fares",
            "deleted": True,
        },
        status=200,
    )
