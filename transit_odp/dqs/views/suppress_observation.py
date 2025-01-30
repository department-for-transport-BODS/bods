from django.db import transaction
from transit_odp.dqs.models import ObservationResults
from transit_odp.organisation.models import ConsumerFeedback, Dataset
from transit_odp.dqs.constants import Level
from rest_framework.response import Response
from rest_framework import viewsets, status as ResponseStatus
from transit_odp.users.models import User
from transit_odp.dqs.constants import Checks
from django.shortcuts import get_object_or_404


class SuppressObservationView(viewsets.ViewSet):
    """
    Suppress Observation view to update the observation result
    """

    queryset = ObservationResults.objects.all()

    def suppress_observation(self, request, **kwargs):
        """Action to suppress the observation result"""

        request_data = request.data
        session_data = request.session
        org_id = self.kwargs.get("pk1", None)
        report_id = self.kwargs.get("report_id", None)

        if session_data and session_data.get("_auth_user_id") and org_id:
            auth_user_id = session_data.get("_auth_user_id")
            users = User.objects.filter(id=auth_user_id)
            if len(users):
                user = users[0]
                organisation_ids = set(user.organisations.values_list("id", flat=True))
                org_id = int(org_id)
                if org_id not in organisation_ids:
                    return Response(
                        {"error": "Unauthorised access"},
                        status=ResponseStatus.HTTP_401_UNAUTHORIZED,
                    )

        dataset = get_object_or_404(
            Dataset.objects.select_related("live_revision"), id=self.kwargs.get("pk")
        )
        revision_id = dataset.live_revision.id
        service_code = request_data.get("service_code", None)
        line_name = request_data.get("line_name", None)
        check = request_data.get("check", None)
        is_suppressed = request_data.get("is_suppressed", False)
        is_feedback = request_data.get("is_feedback", False)
        row_id = request_data.get("row_id", None)

        if not (report_id and org_id and check):
            return Response(
                {"error": "Required parameters are not sent"},
                status=ResponseStatus.HTTP_400_BAD_REQUEST,
            )

        if is_feedback:
            row_count = self.update_observation_feedback(
                org_id, revision_id, service_code, line_name, is_suppressed, row_id
            )
        else:
            row_count = self.update_observation_results(
                report_id, check, service_code, line_name, is_suppressed
            )

        return Response(
            {"status": f"Updated successfully {row_count} rows"},
            status=ResponseStatus.HTTP_200_OK,
        )

    def update_observation_results(
        self,
        report_id: int,
        check: Checks,
        service_code: str,
        line_name: str,
        is_suppressed: bool,
    ) -> int:
        """
        Update the dqs observation results table with the is_suppressed flag
        """
        observations = ObservationResults.objects.filter(
            taskresults__dataquality_report_id=report_id,
            taskresults__checks__observation=check,
            taskresults__checks__importance=Level.advisory.value,
        )
        if service_code and line_name:
            observations = observations.filter(
                taskresults__transmodel_txcfileattributes__service_code=service_code,
                taskresults__transmodel_txcfileattributes__service_txcfileattributes__name=line_name,
            )

        observation_count = len(observations)

        with transaction.atomic():
            observations.update(is_suppressed=is_suppressed)
        return observation_count

    def update_observation_feedback(
        self,
        org_id: int,
        revision_id: int,
        service_code: str,
        line_name: str,
        is_suppressed: bool,
        row_id: int,
    ):
        """
        Update the consumer feedback table with the is_suppressed flag
        """

        feedbacks = ConsumerFeedback.objects.filter(
            revision_id=revision_id,
            organisation_id=org_id,
            service_id__isnull=False,
        )
        if service_code and line_name:
            feedbacks = feedbacks.filter(
                service__service_code=service_code,
                service__service_patterns__line_name=line_name,
            )

        if row_id:
            feedbacks = feedbacks.filter(id=row_id)

        feedbacks = feedbacks.distinct()
        feedback_count = len(feedbacks)

        with transaction.atomic():
            feedbacks.update(is_suppressed=is_suppressed)
        return feedback_count
