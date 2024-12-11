import logging
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict
from django.views.generic import TemplateView
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, views
from rest_framework.response import Response
from requests import RequestException

from transit_odp.api.renders import XMLRender
from transit_odp.api.utils.response_utils import create_xml_error_response

logger = logging.getLogger(__name__)

BODS_USER_API_KEY_PROPERTY = "api_key"


class CancellationsOverview(LoginRequiredMixin, TemplateView):
    """View for Cancellations SIRI API Overview."""

    template_name = "api/cancellations_api_overview.html"


class CancellationsOpenApiView(LoginRequiredMixin, TemplateView):
    """View for Cancellations SIRI API."""

    template_name = "swagger_ui/cancellations.html"


class CancellationsApiView(views.APIView):
    """APIView for returning SIRI-SX XML from the consumer API."""

    permission_classes = (IsAuthenticated,)
    renderer_classes = (XMLRender,)

    def get(self, request, format=None):
        """Get SIRI-SX response from consumer API."""
        url = f"{settings.AVL_CONSUMER_API_BASE_URL}/siri-sx"
        content, status_code = _get_consumer_api_response(url, request.query_params)
        return Response(content, status=status_code, content_type="text/xml")


def _get_consumer_api_response(url: str, query_params: QueryDict):
    """Gets response from CAVL consumer api.

    Args:
        url (str): URL to send request to.
        query_params (QueryDict): Query params to send in get request.

    Returns
        content (str): String representing the body of a response.
        response_status (int): The response status code.
    """
    error_msg = "Unable to process request at this time."
    response_status = status.HTTP_400_BAD_REQUEST
    content = create_xml_error_response(error_msg, response_status)

    params = query_params.copy()
    params.pop(BODS_USER_API_KEY_PROPERTY, None)

    ALLOWED_PARAMETERS = (
        "subscriptionId",
    )

    for key in params:
        if key not in ALLOWED_PARAMETERS:
            error_msg = f"Parameter {key} is not valid."
            content = create_xml_error_response(error_msg, response_status)
            return content, response_status

    try:
        response = requests.get(url, params=params, timeout=60)
    except RequestException:
        return content, response_status

    elapsed_time = response.elapsed.total_seconds()
    logger.info(
        f"Request to Consumer API with params {dict(params)} took {elapsed_time}s "
        f"- status {response.status_code}"
    )
    if response.status_code == 200:
        content = response.content
        response_status = status.HTTP_200_OK

    return content, response_status
