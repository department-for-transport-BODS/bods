from django.http import JsonResponse


from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_gis import filters as gis_filters
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes


# views.py
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Level
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status as ResponseStatus


class SuppressObservationView(viewsets.ViewSet):

    queryset = ObservationResults.objects.all()

    @action(
        methods=["get", "post"],
        detail=False,
        url_path="suppress_observation",
        url_name="suppress_observation",
    )
    def suppress_observation(self, request):
        """Action to suppress the observation result"""

        print(request.body)
        request_data = request.data
        print(f"request_data: {request_data}")
        # return Response(
        #     {"status": f"Updating rows"},
        #     status=ResponseStatus.HTTP_200_OK,
        #     headers={
        #         "Access-Control-Allow-Origin": "*",  # or specify your allowed origin
        #         "Access-Control-Allow-Credentials": "true",
        #     },
        # )

        report_id = request_data.get("report_id", None)
        revision_id = request_data.get("revision_id", None)
        org_id = request_data.get("organisation_id", None)
        service_code = request_data.get("service_code", None)
        line_name = request_data.get("line_name", None)
        check = request_data.get("check", None)
        is_suppressed = request_data.get("is_suppressed", False)

        if not (report_id and revision_id and org_id and check):
            return Response(
                {"error": "Required parameters are not sent"},
                status=ResponseStatus.HTTP_400_BAD_REQUEST,
            )

        observations = ObservationResults.objects.filter(
            taskresults__dataquality_report_id=report_id,
            taskresults__dataquality_report__revision_id=revision_id,
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

        return Response(
            {"status": f"Updated successfully {observation_count} rows"},
            status=ResponseStatus.HTTP_200_OK,
        )
