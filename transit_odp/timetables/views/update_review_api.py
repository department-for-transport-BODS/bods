from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from transit_odp.organisation.models import Dataset
from transit_odp.timetables.views.api import (
    AUTH_REQUIRED_ERROR,
    ORG_ACCESS_REQUIRED_ERROR,
    ORG_NOT_FOUND_ERROR,
    _authenticate_user,
    _get_user_org,
)
from transit_odp.users.constants import AccountType

DATASET_NOT_FOUND_ERROR = "Dataset not found"


@require_GET
def get_timetables_update_success_api(request, pk1, pk):
    """Context for the timetable "Data set published" and "Data set updated" pages.

    Mirrors ``RevisionPublishSuccessView`` and ``RevisionUpdateSuccessView``,
    which share a template and queryset: PTI compliance is taken from the live
    revision of the dataset.
    """
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user or user.account_type == AccountType.abods_user.value:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    if _get_user_org(user, pk1) is None:
        return JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    dataset = (
        Dataset.objects.filter(id=pk, organisation_id=pk1)
        .add_is_live_pti_compliant()
        .first()
    )
    if dataset is None:
        return JsonResponse({"error": DATASET_NOT_FOUND_ERROR}, status=404)

    return JsonResponse(
        {
            "isPtiCompliant": bool(dataset.is_pti_compliant),
            "ptiEnforcedDate": settings.PTI_ENFORCED_DATE.date().isoformat(),
        }
    )
