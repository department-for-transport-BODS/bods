import logging
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, views
from rest_framework.response import Response
from requests import RequestException

from transit_odp.api.renders import XMLRender
from transit_odp.api.utils.response_utils import create_xml_error_response
from transit_odp.api.validators import validate_api_parameter_keys, validate_api_parameter_values

logger = logging.getLogger(__name__)

valid_parameters = [
    "api_key"
]

class DisruptionsOpenApiView(LoginRequiredMixin, TemplateView):
    """View for Disruptions SIRI API."""

    template_name = "swagger_ui/disruptions.html"


class DisruptionsApiView(views.APIView):
    """APIView for returning SIRI SX XML from the consumer API."""

    permission_classes = (IsAuthenticated,)
    renderer_classes = (XMLRender,)

    def get(self, format=None):
        """Get SIRI SX response from consumer API."""
        url = settings.DISRUPTIONS_API_URL
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        # Check for invalid query parameter keys and values
        invalid_parameter_keys = validate_api_parameter_keys(
            self.request.query_params, valid_parameters
        )
        invalid_parameter_values = validate_api_parameter_values(
            self.request.query_params
        )
        # TODO could be refactored to handle invalid keys and values in the
        # same Response
        if len(invalid_parameter_keys) > 0:
            content = {"Unsupported query parameter": invalid_parameter_keys}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        if len(invalid_parameter_values) > 0:
            content = {
                "Unsupported query parameter value for": invalid_parameter_values
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        content, status_code = _get_consumer_api_response(url, headers)
        return Response(content, status=status_code, content_type="text/xml")


def _get_consumer_api_response(url: str, headers: object):
    """Gets response from disruptions consumer api.

    Args:
        url (str): URL to send request to.

    Returns
        content (str): String representing the body of a response.
        response_status (int): The response status code.
    """
    error_msg = "Unable to process request at this time."
    response_status = status.HTTP_400_BAD_REQUEST
    content = create_xml_error_response(error_msg, response_status)

    try:
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

    return content, response_status
