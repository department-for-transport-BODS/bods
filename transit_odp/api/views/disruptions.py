import logging
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, views
from rest_framework.response import Response
from requests import RequestException

from transit_odp.api.renders import XMLRender
from transit_odp.api.utils.response_utils import create_xml_error_response

logger = logging.getLogger(__name__)


class DisruptionsOpenApiView(LoginRequiredMixin, TemplateView):
    """View for Disruptions SIRI API."""
    template_name = "swagger_ui/disruptions.html"


class DisruptionsApiView(views.APIView):
    """APIView for returning SIRI SX XML from the consumer API."""
    permission_classes = (IsAuthenticated,)
    renderer_classes = (XMLRender,)

    def get(self, format=None):
        """Get SIRI SX response from consumer API."""
        error_msg = "Unable to process request"
        response_status = status.HTTP_400_BAD_REQUEST
        content = create_xml_error_response(error_msg, response_status)
        url = settings.SIRI_API_URL

        try:
            headers = {
                "x-api-key": settings.SIRI_API_KEY
            }
            response = requests.get(url, headers=headers, timeout=60)
        except RequestException:
            return content, response_status

        elapsed_time = response.elapsed.total_seconds()
        logger.info(
            f"Request to SIRI Consumer API took {elapsed_time}s "
            f"- status {response.status_code}"
        )
        if response.status_code == 200:
            content = response.content
            response_status = status.HTTP_200_OK

        return Response(content, status=response_status, content_type="text/xml")
