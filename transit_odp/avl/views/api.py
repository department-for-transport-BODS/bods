import uuid

from django.contrib.auth import get_user
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django_hosts import reverse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

import config.hosts
from transit_odp.avl.forms import (
    AvlFeedDescriptionForm,
    AvlFeedUploadForm,
    EditFeedDescriptionForm,
)
from transit_odp.avl.forms import AVLFeedCommentForm
from transit_odp.avl.models import (
    CAVLValidationTaskResult,
    PostPublishingCheckReport,
    PPCReportType,
)
from transit_odp.avl.tasks import task_validate_avl_feed
from transit_odp.avl.views.review import ERROR_DESCRIPTIONS
from transit_odp.avl.views.utils import get_validation_task_result_from_revision_id
import pytz
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import (
    Dataset,
    DatasetMetadata,
    DatasetRevision,
    Organisation,
)
from transit_odp.publish.forms import dataset
from transit_odp.timetables.tasks import delete_dataset_revision


_jwt_auth = JWTAuthentication()
FIRST_PUBLICATION_COMMENT = "First publication"
AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ACCESS_REQUIRED_ERROR = "Org user access required"
ORG_NOT_FOUND_ERROR = "Organisation not found"
REVISION_NOT_FOUND_ERROR = "Dataset revision not found"
ExpiredStatus = FeedStatus.expired.value
ALLOW_DRAFT_DETAIL_FALLBACK = True


def _authenticate_jwt(request):
    try:
        result = _jwt_auth.authenticate(request)
    except (InvalidToken, TokenError):
        return None
    if result is None:
        return None
    user, _token = result
    return user


def _authenticate_user(request):
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


def _get_dataset_for_org(org_id, dataset_id):
    return (
        Dataset.objects.filter(
            id=dataset_id,
            organisation_id=org_id,
        )
        .order_by("-id")
        .first()
    )


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
            JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403),
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
                JsonResponse({"error": REVISION_NOT_FOUND_ERROR}, status=404),
            )

    return user, organisation, revision, None


def _iso_or_none(value):
    if value is None:
        return None
    return value.isoformat()


def _get_review_state(revision):
    task = get_validation_task_result_from_revision_id(revision.id)

    if task is None or not task.result:
        return True, 0, None

    progress = 100
    error = ERROR_DESCRIPTIONS.get(task.result)
    return False, progress, error


@csrf_exempt
@require_POST
def create_avl_dataset_api(request, pk1):
    user, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return error_response

    description_form = AvlFeedDescriptionForm(data=request.POST)
    if not description_form.is_valid():
        return JsonResponse(
            {
                "error": "Description validation failed",
                "field_errors": description_form.errors,
            },
            status=400,
        )

    upload_form = AvlFeedUploadForm(data=request.POST)
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
    all_data["status"] = "success"

    with transaction.atomic():
        dataset = Dataset.objects.create(
            contact=user,
            organisation_id=organisation.id,
            dataset_type=DatasetType.AVL.value,
        )

        revision = DatasetRevision.objects.filter(
            Q(dataset=dataset) & Q(is_published=False)
        ).update_or_create(dataset=dataset, is_published=False, defaults=all_data,)[0]

        task_id = uuid.uuid4()
        CAVLValidationTaskResult.objects.create(
            revision=revision,
            task_id=task_id,
            status=CAVLValidationTaskResult.SUCCESS,
        )

        transaction.on_commit(lambda: task_validate_avl_feed.delay(task_id))

    review_url = f"/publish/org/{organisation.id}/dataset/avl/{dataset.id}/review"

    return JsonResponse({"redirect": review_url}, status=201)


@csrf_exempt
@require_GET
def get_avl_review_status_api(request, pk1, pk):
    _, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    loading, progress, error = _get_review_state(revision)

    schema_version = None
    try:
        metadata = DatasetMetadata.objects.get(revision=revision)
        schema_version = metadata.schema_version
    except DatasetMetadata.DoesNotExist:
        pass

    last_modified_user = None
    if revision.last_modified_user is not None:
        last_modified_user = revision.last_modified_user.username

    return JsonResponse(
        {
            "datasetId": revision.dataset_id,
            "revisionId": revision.id,
            "hasLiveRevision": revision.dataset.live_revision is not None,
            "status": revision.status,
            "progress": progress,
            "loading": loading,
            "name": revision.name,
            "description": revision.description,
            "shortDescription": revision.short_description,
            "comment": revision.comment,
            "urlLink": revision.url_link,
            "requestorRef": revision.requestor_ref,
            "ownerName": revision.dataset.organisation.name,
            "siriVersion": schema_version,
            "lastModified": _iso_or_none(revision.modified),
            "lastModifiedUser": last_modified_user,
            "error": error,
        },
        status=200,
    )


@csrf_exempt
@require_POST
def publish_avl_dataset_api(request, pk1, pk):
    user, _, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    loading, _progress, error = _get_review_state(revision)
    if loading:
        return JsonResponse({"error": "Dataset is still processing"}, status=409)

    if error is not None:
        return JsonResponse({"error": error}, status=409)

    try:
        if not revision.is_published:
            revision.publish(user)
    except Exception:
        return JsonResponse(
            {"redirect": f"/publish/org/{pk1}/dataset/avl/{pk}/error"},
            status=200,
        )

    return JsonResponse(
        {
            "redirect": f"/publish/org/{pk1}/dataset/avl/{pk}/success",
            "published": True,
        },
        status=200,
    )


@csrf_exempt
@require_POST
def delete_avl_dataset_api(request, pk1, pk):
    _user, _org, revision, error_response = _get_request_context(request, pk1, pk)
    if error_response is not None:
        return error_response

    if not revision.is_published or revision.status == ExpiredStatus:
        delete_dataset_revision.delay(revision.id)

    return JsonResponse(
        {
            "redirect": f"/publish/org/{pk1}/dataset/avl/{pk}/delete/success",
            "deleted": True,
        },
        status=200,
    )


@csrf_exempt
@require_POST
def update_avl_dataset_api(request, pk1, pk):
    user = _authenticate_user(request)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    organisation = _get_user_org(user, pk1)
    if organisation is None:
        return JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    dataset = _get_dataset_for_org(organisation.id, pk)
    if dataset is None:
        return JsonResponse({"error": REVISION_NOT_FOUND_ERROR}, status=404)

    revision = DatasetRevision.objects.filter(
        dataset=dataset, is_published=False
    ).first()
    if revision is None:
        revision = dataset.start_revision()
        revision.url_link = ""

    comment_form = AVLFeedCommentForm(
        data=request.POST, instance=revision, is_update=True
    )
    if not comment_form.is_valid():
        return JsonResponse(
            {
                "error": "Comment validation failed",
                "field_errors": comment_form.errors,
            },
            status=400,
        )

    upload_form = AvlFeedUploadForm(
        data=request.POST, instance=revision, is_update=True
    )
    if not upload_form.is_valid():
        return JsonResponse(
            {
                "error": "Upload validation failed",
                "field_errors": upload_form.errors,
            },
            status=400,
        )

    all_data = {}
    all_data.update(comment_form.cleaned_data)
    all_data.update(upload_form.cleaned_data)
    all_data["last_modified_user"] = user
    all_data["status"] = "success"

    with transaction.atomic():
        for key, value in all_data.items():
            setattr(revision, key, value)
        revision.save()

        task_id = uuid.uuid4()
        CAVLValidationTaskResult.objects.create(
            revision=revision,
            task_id=task_id,
            status=CAVLValidationTaskResult.STARTED,
        )

        transaction.on_commit(lambda: task_validate_avl_feed.delay(task_id))

    review_url = (
        f"/publish/org/{organisation.id}/dataset/avl/{dataset.id}/update/review"
    )

    return JsonResponse({"redirect": review_url}, status=200)


@csrf_exempt
@require_GET
def get_avl_dataset_edit_api(request, pk1, pk):
    """Fetch existing description fields for AVL dataset edit page."""
    user = _authenticate_user(request)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    organisation = _get_user_org(user, pk1)
    if organisation is None:
        return JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    dataset = _get_dataset_for_org(organisation.id, pk)
    if dataset is None:
        return JsonResponse({"error": "Dataset not found"}, status=404)

    revision = dataset.live_revision
    if revision is None and ALLOW_DRAFT_DETAIL_FALLBACK:
        revision = _get_revision_for_dataset(organisation.id, pk)

    if revision is None:
        return JsonResponse({"error": "Dataset revision not found"}, status=404)

    return JsonResponse(
        {
            "datasetId": dataset.id,
            "name": revision.name or "",
            "description": revision.description or "",
            "shortDescription": revision.short_description or "",
        },
        status=200,
    )


@csrf_exempt
@require_POST
def edit_avl_dataset_description_api(request, pk1, pk):
    """Save AVL description fields edited from feed detail page."""
    user = _authenticate_user(request)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    organisation = _get_user_org(user, pk1)
    if organisation is None:
        return JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    dataset = _get_dataset_for_org(organisation.id, pk)
    if dataset is None:
        return JsonResponse({"error": "Dataset not found"}, status=404)

    revision = dataset.live_revision
    if revision is None and ALLOW_DRAFT_DETAIL_FALLBACK:
        revision = _get_revision_for_dataset(organisation.id, pk)

    if revision is None:
        return JsonResponse({"error": "Dataset revision not found"}, status=404)

    form = EditFeedDescriptionForm(data=request.POST, instance=revision)
    if not form.is_valid():
        return JsonResponse(
            {
                "error": "Description validation failed",
                "field_errors": form.errors,
            },
            status=400,
        )

    revision.description = form.cleaned_data["description"]
    revision.short_description = form.cleaned_data["short_description"]
    revision.save()

    return JsonResponse(
        {
            "redirect": f"/publish/org/{organisation.id}/dataset/avl/{dataset.id}",
        },
        status=200,
    )


@csrf_exempt
@require_GET
def list_avl_datasets_api(request, pk1):
    user, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return error_response

    tab = request.GET.get("tab", "active")
    sort_by = request.GET.get("sort_by", "modified")
    order = request.GET.get("order", "desc")

    # Map frontend column names to model fields
    sort_field_map = {
        "status": "live_revision__status",
        "name": "live_revision__name",
        "percent_matching": "percent_matching",
        "avl_feed_last_checked": "avl_feed_last_checked",
        "modified": "modified",
    }

    sort_field = sort_field_map.get(sort_by, "modified")
    if order == "asc":
        sort_field = sort_field
    else:
        sort_field = f"-{sort_field}"

    qs = (
        Dataset.objects.filter(
            organisation_id=organisation.id,
            dataset_type=DatasetType.AVL.value,
        )
        .select_related("live_revision")
        .order_by(sort_field)
    )

    if tab == "active":
        qs = qs.filter(live_revision__status="live")
    elif tab == "draft":
        qs = qs.filter(
            live_revision__status__in=[
                "success",
                "draft",
                "indexing",
                "pending",
                "processing",
            ]
        )
    elif tab == "archive":
        qs = qs.filter(live_revision__status__in=["inactive", "expired"])
    else:
        qs = qs.filter(live_revision__status="live")

    results = []
    for dataset in qs:
        revision = dataset.live_revision
        if revision is None:
            continue
        results.append(
            {
                "id": dataset.id,
                "name": revision.name or "",
                "status": revision.status,
                "short_description": revision.short_description or "",
                "avl_feed_last_checked": (
                    dataset.avl_feed_last_checked.isoformat()
                    if dataset.avl_feed_last_checked
                    else None
                ),
                "modified": revision.modified.isoformat()
                if revision.modified
                else None,
            }
        )

    return JsonResponse({"count": len(results), "results": results})


@csrf_exempt
@require_GET
def get_avl_changelog_api(request, pk1, pk):
    """Fetch paginated changelog entries for an AVL dataset."""
    user = _authenticate_user(request)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    organisation = _get_user_org(user, pk1)
    if organisation is None:
        return JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    dataset = _get_dataset_for_org(pk1, pk)
    if dataset is None:
        return JsonResponse({"error": "Dataset not found"}, status=404)

    revisions_qs = (
        DatasetRevision.objects.filter(dataset=dataset)
        .get_published()
        .prefetch_related("errors")
        .order_by("-created")
    )

    page_value = request.GET.get("page", "1")
    try:
        page_number = max(1, int(page_value))
    except (TypeError, ValueError):
        page_number = 1

    paginator = Paginator(revisions_qs, 10)
    page_obj = paginator.get_page(page_number)

    feed_name = ""
    if dataset.live_revision is not None and dataset.live_revision.name:
        feed_name = dataset.live_revision.name
    else:
        latest_published = revisions_qs.first()
        if latest_published is not None:
            feed_name = latest_published.name or ""
        else:
            draft_revision = _get_revision_for_dataset(pk1, pk)
            if draft_revision is not None:
                feed_name = draft_revision.name or ""

    results = []
    for revision in page_obj.object_list:
        error_descriptions = []
        if revision.status == "error":
            error_descriptions = [error.description for error in revision.errors.all()]

        updated_at = revision.published_at or revision.created
        results.append(
            {
                "revisionId": revision.id,
                "status": revision.status,
                "comment": revision.comment or "",
                "updatedAt": _iso_or_none(updated_at),
                "errors": error_descriptions,
            }
        )

    return JsonResponse(
        {
            "datasetId": dataset.id,
            "feedName": feed_name,
            "count": paginator.count,
            "page": page_obj.number,
            "pageSize": paginator.per_page,
            "totalPages": paginator.num_pages,
            "hasNext": page_obj.has_next(),
            "hasPrevious": page_obj.has_previous(),
            "results": results,
        },
        status=200,
    )


@csrf_exempt
@require_GET
def get_avl_feed_detail_api(request, pk1, pk):
    """Fetch detailed information for a published AVL feed."""
    user = _authenticate_user(request)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    organisation = _get_user_org(user, pk1)
    if organisation is None:
        return JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    # Get published dataset (not draft revision)
    dataset = _get_dataset_for_org(pk1, pk)
    if dataset is None:
        return JsonResponse({"error": "Published dataset not found"}, status=404)

    # Use live revision if available; optional fallback to draft for local UI testing
    revision = dataset.live_revision
    if revision is None and ALLOW_DRAFT_DETAIL_FALLBACK:
        revision = _get_revision_for_dataset(pk1, pk)

    if revision is None:
        return JsonResponse({"error": "Dataset not found"}, status=404)

    # Get last modified user
    last_modified_username = None
    if revision.last_modified_user is not None:
        last_modified_username = revision.last_modified_user.username

    # Get published by user
    published_by = None
    if revision.published_by is not None:
        published_by = revision.published_by.username

    # Get SIRI version from metadata
    siri_version = None
    try:
        metadata = DatasetMetadata.objects.get(revision=revision)
        siri_version = metadata.schema_version
    except DatasetMetadata.DoesNotExist:
        pass

    # Get last server update (avl_feed_last_checked), fallback to revision modified
    last_server_update = ""
    if dataset.avl_feed_last_checked is not None:
        last_server_update = dataset.avl_feed_last_checked.astimezone(
            pytz.timezone("Europe/London")
        ).strftime("%d %b %Y %H:%M")
    elif revision.modified is not None:
        last_server_update = revision.modified.astimezone(
            pytz.timezone("Europe/London")
        ).strftime("%d %b %Y %H:%M")

    # Get PPC weekly matching score
    ppc_weekly_score = None
    try:
        ppc_avl_dataset = (
            PostPublishingCheckReport.objects.filter(granularity="weekly")
            .filter(dataset__id=dataset.id)
            .order_by("-created")
        ).first()
        if ppc_avl_dataset and ppc_avl_dataset.vehicle_activities_analysed > 0:
            ppc_weekly_score = (
                str(
                    ppc_avl_dataset.vehicle_activities_completely_matching
                    * 100
                    // ppc_avl_dataset.vehicle_activities_analysed,
                )
                + "%"
            )
    except (Exception,):
        pass

    return JsonResponse(
        {
            "datasetId": dataset.id,
            "name": revision.name or "",
            "description": revision.description or "",
            "shortDescription": revision.short_description or "",
            "status": revision.status,
            "organisationName": dataset.organisation.name,
            "organisationId": dataset.organisation_id,
            "siriVersion": siri_version or "",
            "urlLink": revision.url_link or "",
            "lastModified": _iso_or_none(revision.modified),
            "lastModifiedUser": last_modified_username,
            "lastServerUpdate": last_server_update,
            "publishedBy": published_by,
            "publishedAt": _iso_or_none(revision.published_at),
            "avlComplianceStatus": getattr(dataset, "avl_compliance_status_cached", "")
            or "",
            "avlTimetablesMatching": ppc_weekly_score,
            "isDummy": dataset.is_dummy,
        },
        status=200,
    )
