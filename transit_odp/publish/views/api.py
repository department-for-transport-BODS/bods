import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET

import pandas as pd
import requests
from waffle import flag_is_active
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import AllowAny, IsAuthenticated
from transit_odp.api.views.avl import _get_consumer_api_response
from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import DatasetRevision
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
    get_avl_requires_attention_line_level_data,
    get_requires_attention_line_level_data,
)
from transit_odp.publish.views.utils import get_simulated_progress
from transit_odp.avl.post_publishing_checks.models.siri import Siri
from transit_odp.publish.views.utils import get_vehicle_activity_dict

logger = logging.getLogger(__name__)

AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ACCESS_REQUIRED_ERROR = "Org user access required"

PROGRESS_TIMEOUT = 2
COMPLETED = 100


class ProgressAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        """Get a dataset revision object from a dataset id."""
        try:
            return DatasetRevision.objects.filter(
                dataset_id=pk,
                dataset__organisation__in=self.request.user.organisations.all(),
            ).latest()
        except DatasetRevision.DoesNotExist as exc:
            raise Http404 from exc

    def get_avl_progress(self, revision):
        """Get the progress of a currently processing AVL datafeed."""
        try:
            task = CAVLValidationTaskResult.objects.filter(
                revision_id=revision.id
            ).latest("created")
        except CAVLValidationTaskResult.DoesNotExist:
            msg = f"Could not find CAVLValidationTaskResult for revision: {revision.id}"
            logger.warning(msg, exc_info=True)
            return COMPLETED

        if task.status in [task.SUCCESS, task.FAILURE]:
            progress = COMPLETED
        else:
            # We need to fake the progression
            max_minutes = timedelta(minutes=PROGRESS_TIMEOUT)
            progress = get_simulated_progress(task.created, max_minutes)
            if progress >= 99:
                # if we get here then something has gone wrong
                task.to_timeout_error()
                task.save()
        return progress

    def get_timetable_progress(self, revision):
        """Get the progress of a currently processing timetables dataset."""
        progress = 0
        task = revision.etl_results.order_by("-id").first()
        if task is not None:
            progress = task.progress
            if task.error_code:
                progress = COMPLETED
        return progress

    def get_fares_progress(self, revision):
        """Get the progress of a currently processing fares dataset."""
        progress = 0
        task = revision.etl_results.order_by("-id").first()
        if task is not None:
            progress = task.progress
            if task.error_code:
                progress = COMPLETED
        return progress

    def get(self, request, pk, format=None):
        """Get the progress of a dataset revision."""
        revision = self.get_object(pk)
        progress = 0
        if revision.dataset.dataset_type == DatasetType.TIMETABLE:
            progress = self.get_timetable_progress(revision)

        elif revision.dataset.dataset_type == DatasetType.AVL:
            progress = self.get_avl_progress(revision)

        elif revision.dataset.dataset_type == DatasetType.FARES:
            progress = self.get_fares_progress(revision)

        return Response({"progress": progress, "status": revision.status})


class AVLRealTimeDataView(APIView):
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        url = f"{settings.AVL_CONSUMER_API_BASE_URL}/siri-vm"

        params = request.query_params.copy()
        tt_journey_codes = params.pop("journey_code", None)

        content, status_code = _get_consumer_api_response(url, params)

        siri = Siri.from_string(content)
        service_delivery = siri.service_delivery
        vehicle_activities = (
            service_delivery.vehicle_monitoring_delivery.vehicle_activities
        )
        vehicle_activity_dict = get_vehicle_activity_dict(
            vehicle_activities, tt_journey_codes
        )

        return Response(vehicle_activity_dict, status=200)


@require_GET
def get_agent_dashboard_organisations_api(request):
    """Return the requesting user's organisations with per-type requires-attention
    counts, mirroring AgentDashboardView.get_table_data()."""
    user = get_user(request)
    if user is None or not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    search_term = request.GET.get("q", "").strip()
    memberships = user.organisations.through.objects.filter(user=user).select_related(
        "organisation"
    )
    if search_term:
        memberships = memberships.filter(organisation__name__icontains=search_term)
    memberships = memberships.order_by("organisation__name")

    is_avl_require_attention_active = flag_is_active(
        "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
    )
    is_fares_require_attention_active = flag_is_active(
        "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
    )
    is_operator_prefetch_sra_active = flag_is_active(
        "", FeatureFlags.OPERATOR_PREFETCH_SRA.value
    )

    uncounted_activity_df = pd.DataFrame()
    synced_in_last_month = []
    if is_avl_require_attention_active and not is_operator_prefetch_sra_active:
        uncounted_activity_df = get_vehicle_activity_operatorref_linename()
        synced_in_last_month = AbodsRegistery().records()

    results = []
    for membership in memberships:
        organisation = membership.organisation

        if is_operator_prefetch_sra_active:
            timetable_sra = organisation.timetable_sra
            avl_sra = organisation.avl_sra
            fares_sra = organisation.fares_sra
        else:
            timetable_sra = len(get_requires_attention_line_level_data(organisation.id))
            avl_sra = (
                len(
                    get_avl_requires_attention_line_level_data(
                        organisation.id, uncounted_activity_df, synced_in_last_month
                    )
                )
                if is_avl_require_attention_active
                else 0
            )
            fares_sra = (
                len(
                    FaresRequiresAttention(
                        organisation.id
                    ).get_fares_requires_attention_line_level_data()
                )
                if is_fares_require_attention_active
                else 0
            )

        results.append(
            {
                "id": organisation.id,
                "name": organisation.name,
                "requiresAttention": timetable_sra,
                "avlRequiresAttention": avl_sra,
                "faresRequiresAttention": fares_sra,
            }
        )

    return JsonResponse({"results": results}, status=200)
