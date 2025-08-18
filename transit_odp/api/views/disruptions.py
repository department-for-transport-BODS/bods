import logging
import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, views
from rest_framework.response import Response
from requests import RequestException
from django.http import HttpResponse
from waffle import flag_is_active

from transit_odp.api.renders import BinRenderer, ProtoBufRenderer, XMLRender
from transit_odp.api.utils.response_utils import create_xml_error_response

logger = logging.getLogger(__name__)

BODS_USER_API_KEY_PROPERTY = "api_key"


class DisruptionsOverview(LoginRequiredMixin, TemplateView):
    """View for Disruptions SIRI API Overview."""

    template_name = "api/disruptions_api_overview.html"

    def get(self, request, *args, **kwargs):
        """Check whether cancellations feature flag is active before rendering page."""
        is_cancellations_live = flag_is_active("", "is_cancellations_live")
        if is_cancellations_live is False:
            return HttpResponse(status=404)
        return super().get(request, *args, **kwargs)


class DisruptionsOpenApiView(LoginRequiredMixin, TemplateView):
    """View for Disruptions SIRI API."""

    template_name = "swagger_ui/disruptions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_gtfs_service_alerts_live"] = flag_is_active(
            "", "is_gtfs_service_alerts_live"
        )
        return context


class DisruptionsApiView(views.APIView):
    """APIView for returning SIRI-SX XML from the consumer API."""

    permission_classes = (IsAuthenticated,)
    renderer_classes = (XMLRender,)

    def get(self, format=None):
        """Get SIRI-SX response from consumer API."""
        url = f"{settings.DISRUPTIONS_API_BASE_URL}/siri-sx"
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        content, status_code = _get_consumer_api_response(url, headers)
        return Response(content, status=status_code, content_type="text/xml")


class DisruptionsGtfsRtServiceAlertsApiView(views.APIView):
    """APIView for returning GTFS RT from the consumer API."""

    permission_classes = (IsAuthenticated,)
    renderer_classes = (BinRenderer, ProtoBufRenderer)

    def get(self, request, format=None):
        """Get GTFS RT response from consumer API."""

        url = f"{settings.GTFS_API_BASE_URL}/gtfs-rt/service-alerts"
        content, status_code = _get_gtfs_rt_response(url)

        return Response(content, status=status_code)


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


def _get_gtfs_rt_response(url: str):
    """Gets GTFS RT response from CAVL consumer api.

    Args:
        url (str): URL to send request to.


    Returns
        content (str): String representing the body of a response.
        response_status (int): The response status code.
    """
    error_msg = "Unable to process request at this time."
    response_status = status.HTTP_400_BAD_REQUEST
    content = f"{response_status}: {error_msg}."

    params = BODS_USER_API_KEY_PROPERTY if BODS_USER_API_KEY_PROPERTY else None

    try:
        response = requests.get(url, params=params, timeout=60)
    except RequestException:
        return content, response_status

    if response.status_code == 200:
        content = response.content
        response_status = status.HTTP_200_OK

    return content, response_status
