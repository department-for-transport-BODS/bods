"""
JSON API for the Next.js "Edit description" pages.

Mirrors ``EditDescriptionBaseView`` and its timetable and fares subclasses:
``dataset-edit`` edits the live revision and ``revision-edit`` edits the latest
revision of the data set.
"""
from django.contrib.auth import get_user
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from transit_odp.fares.forms import (
    EditFeedDescriptionForm as FaresEditFeedDescriptionForm,
)
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset
from transit_odp.publish.forms import EditFeedDescriptionForm
from transit_odp.users.constants import AccountType

AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ACCESS_REQUIRED_ERROR = "Org user access required"
DATASET_NOT_FOUND_ERROR = "Dataset not found"
REVISION_NOT_FOUND_ERROR = "Dataset revision not found"
VALIDATION_ERROR = "Description validation failed"

FORM_CLASSES = {
    DatasetType.TIMETABLE.value: EditFeedDescriptionForm,
    DatasetType.FARES.value: FaresEditFeedDescriptionForm,
}


def _get_revision(request, org_id, dataset_id, dataset_type, is_live):
    user = get_user(request)
    if not user.is_authenticated:
        return None, JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    # Same rules as OrgUserViewMixin.has_permission.
    if (
        not user.is_org_user
        or user.account_type == AccountType.abods_user.value
        or not user.organisations.filter(id=org_id).exists()
    ):
        return None, JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    dataset = Dataset.objects.filter(
        id=dataset_id, organisation_id=org_id, dataset_type=dataset_type
    ).first()
    if dataset is None:
        return None, JsonResponse({"error": DATASET_NOT_FOUND_ERROR}, status=404)

    if is_live:
        revision = dataset.live_revision
    else:
        revision = dataset.revisions.order_by("-id").first()

    if revision is None:
        return None, JsonResponse({"error": REVISION_NOT_FOUND_ERROR}, status=404)

    return revision, None


def _revision_to_json(revision):
    return {
        "datasetId": revision.dataset_id,
        "name": revision.name or "",
        "description": revision.description or "",
        "shortDescription": revision.short_description or "",
        "isRevisionUpdate": revision.dataset.live_revision_id is not None,
    }


def _get_description(request, pk1, pk, dataset_type, is_live):
    revision, error_response = _get_revision(request, pk1, pk, dataset_type, is_live)
    if error_response is not None:
        return error_response
    return JsonResponse(_revision_to_json(revision), status=200)


def _save_description(request, pk1, pk, dataset_type, is_live):
    revision, error_response = _get_revision(request, pk1, pk, dataset_type, is_live)
    if error_response is not None:
        return error_response

    form = FORM_CLASSES[dataset_type](data=request.POST, instance=revision)
    if not form.is_valid():
        return JsonResponse(
            {"error": VALIDATION_ERROR, "field_errors": form.errors}, status=400
        )

    revision.description = form.cleaned_data["description"]
    revision.short_description = form.cleaned_data["short_description"]
    revision.save()
    return JsonResponse(_revision_to_json(revision), status=200)


@require_GET
def get_timetables_dataset_edit_api(request, pk1, pk):
    return _get_description(request, pk1, pk, DatasetType.TIMETABLE.value, True)


@require_POST
def save_timetables_dataset_edit_api(request, pk1, pk):
    return _save_description(request, pk1, pk, DatasetType.TIMETABLE.value, True)


@require_GET
def get_timetables_revision_edit_api(request, pk1, pk):
    return _get_description(request, pk1, pk, DatasetType.TIMETABLE.value, False)


@require_POST
def save_timetables_revision_edit_api(request, pk1, pk):
    return _save_description(request, pk1, pk, DatasetType.TIMETABLE.value, False)


@require_GET
def get_fares_dataset_edit_api(request, pk1, pk):
    return _get_description(request, pk1, pk, DatasetType.FARES.value, True)


@require_POST
def save_fares_dataset_edit_api(request, pk1, pk):
    return _save_description(request, pk1, pk, DatasetType.FARES.value, True)


@require_GET
def get_fares_revision_edit_api(request, pk1, pk):
    return _get_description(request, pk1, pk, DatasetType.FARES.value, False)


@require_POST
def save_fares_revision_edit_api(request, pk1, pk):
    return _save_description(request, pk1, pk, DatasetType.FARES.value, False)
