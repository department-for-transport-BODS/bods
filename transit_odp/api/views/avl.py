import logging

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict
from django.views.generic import TemplateView
from requests import RequestException
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from waffle import flag_is_active

from transit_odp.api.renders import BinRenderer, ProtoBufRenderer, XMLRender
from transit_odp.api.utils.response_utils import create_xml_error_response
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset

logger = logging.getLogger(__name__)

API_KEY = "api_key"
PARAMETERS = (
    "boundingBox",
    "destinationRef",
    "lineRef",
    "operatorRef",
    "originRef",
    "producerRef",
    "vehicleRef",
)


class AVLOpenApiView(LoginRequiredMixin, TemplateView):
    template_name = "swagger_ui/avl.html"


class AVLApiView(views.APIView):
    """APIView for returning SIRI VM XML from the consumer API."""

    permission_classes = (IsAuthenticated,)
    renderer_classes = (XMLRender,)

    def get(self, request, format=None):
        """Get SIRI VM response from consumer API."""
        url = f"{settings.AVL_CONSUMER_API_BASE_URL}/siri-vm"
        content, status_code = _get_consumer_api_response(url, request.query_params)
        return Response(content, status=status_code, content_type="text/xml")


class AVLDetailApiView(views.APIView):
    """APIView for returning SIRI VM XML from the consumer API."""

    permission_classes = (IsAuthenticated,)
    renderer_classes = (XMLRender,)

    def get(self, request, pk=-1, format=None):
        """Get SIRI VM response from consumer API."""
        url = f"{settings.AVL_CONSUMER_API_BASE_URL}/siri-vm?subscriptionId={pk}"
        print(url)
        # try:
        #     Dataset.objects.get(pk=pk, dataset_type=DatasetType.AVL)
        # except Dataset.DoesNotExist:
        #     msg = f"Datafeed {pk} does not exist."
        #     content = create_xml_error_response(msg, status.HTTP_404_NOT_FOUND)
        #     return Response(
        #         content, status=status.HTTP_404_NOT_FOUND, content_type="text/xml"
        #     )

        content, status_code = _get_consumer_api_response(url, request.query_params)
        return Response(
            content,
            status=status_code,
            content_type="text/xml",
        )


class AVLGTFSRTApiView(views.APIView):
    """APIView for returning GTFS RT from the consumer API."""

    permission_classes = (IsAuthenticated,)
    renderer_classes = (BinRenderer, ProtoBufRenderer)

    def get(self, request, format=None):
        """Get GTFS RT response from consumer API."""
        is_new_gtfs_api_active = flag_is_active("", "is_new_gtfs_api_active")
        url = (
            f"{settings.GTFS_API_BASE_URL}/gtfs-rt"
            if is_new_gtfs_api_active
            else f"{settings.CAVL_CONSUMER_URL}/gtfsrtfeed"
        )
        content, status_code = _get_gtfs_rt_response(url, request.query_params)

        return Response(content, status=status_code)


def _get_gtfs_rt_response(url: str, query_params: QueryDict):
    """Gets GTFS RT response from CAVL consumer api.

    Args:
        url (str): URL to send request to.
        query_params (QueryDict): Query params to send in get request.

    Returns
        content (str): String representing the body of a response.
        response_status (int): The response status code.
    """
    error_msg = "Unable to process request at this time."
    response_status = status.HTTP_400_BAD_REQUEST
    content = f"{response_status}: {error_msg}."

    params = query_params.copy()
    params.pop(API_KEY, None)

    try:
        response = requests.get(url, params=params, timeout=60)
    except RequestException:
        return content, response_status

    if response.status_code == 200:
        content = response.content
        response_status = status.HTTP_200_OK

    return content, response_status


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
    params.pop(API_KEY, None)

    for key in params:
        if key not in PARAMETERS:
            error_msg = f"Parameter {key} is not valid."
            content = create_xml_error_response(error_msg, response_status)
            return content, response_status

    try:
        response = requests.get(
            url,
            params=params,
            timeout=60,
            headers={"x-api-key": "4DAD5A79-2F67-4F80-B63B-F472AB83BE0A"},
        )
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
