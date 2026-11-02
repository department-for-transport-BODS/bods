from django.http import JsonResponse
from django.views.decorators.http import require_GET
from waffle import flag_is_active

from transit_odp.fares.views.api import _get_request_context
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset

DATASET_NOT_FOUND_ERROR = "Dataset not found"


@require_GET
def get_fares_update_success_api(request, pk1, pk):
    """Context for the fares "Data set updated" page.

    Mirrors ``fares.views.update.RevisionUpdateSuccessView``: when the fares
    validator flag is on, the live revision's validation result decides whether
    the "failed the validation set" paragraph is shown.
    """
    _, organisation, _, error_response = _get_request_context(request, pk1)
    if error_response is not None:
        return error_response

    dataset = Dataset.objects.filter(
        id=pk,
        organisation_id=organisation.id,
        dataset_type=DatasetType.FARES.value,
    ).first()
    if dataset is None:
        return JsonResponse({"error": DATASET_NOT_FOUND_ERROR}, status=404)

    is_fares_validator_active = flag_is_active(request, "is_fares_validator_active")
    validator_error = False
    if is_fares_validator_active and dataset.live_revision_id is not None:
        count = (
            FaresValidationResult.objects.filter(revision_id=dataset.live_revision_id)
            .values_list("count", flat=True)
            .first()
        )
        validator_error = count is not None and count != 0

    return JsonResponse(
        {
            "isFaresValidatorActive": is_fares_validator_active,
            "validatorError": validator_error,
        }
    )
