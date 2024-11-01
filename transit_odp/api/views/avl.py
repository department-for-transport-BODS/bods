import logging
import uuid

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict
from django.views.generic import TemplateView
from requests import RequestException
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from transit_odp.avl.client.cavl import CAVLSubscriptionService
from transit_odp.avl.forms import AvlSubscriptionsSubscribeForm
from waffle import flag_is_active
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django.http import HttpResponseRedirect
from django_hosts import reverse
import config.hosts
from rest_framework.authtoken.models import Token

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


class AVLApiServiceView(LoginRequiredMixin, TemplateView):
    template_name = "api/avl_api_service.html"


class AVLOpenApiView(LoginRequiredMixin, TemplateView):
    template_name = "swagger_ui/avl.html"


class AVLSubscriptionsSubscribeView(LoginRequiredMixin, FormView):
    template_name = "api/avl_subscriptions_subscribe.html"
    form_class = AvlSubscriptionsSubscribeForm
    cavl_subscription_service = CAVLSubscriptionService()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        api_key = Token.objects.get_or_create(user=self.request.user)[0].key
        subscription_id = uuid.uuid4()
        dataset_ids = [form.cleaned_data["dataset_id_1"]]

        if form.cleaned_data["dataset_id_2"]:
            dataset_ids.append(form.cleaned_data["dataset_id_2"])

        if form.cleaned_data["dataset_id_3"]:
            dataset_ids.append(form.cleaned_data["dataset_id_3"])

        if form.cleaned_data["dataset_id_4"]:
            dataset_ids.append(form.cleaned_data["dataset_id_4"])

        if form.cleaned_data["dataset_id_5"]:
            dataset_ids.append(form.cleaned_data["dataset_id_5"])

        self.cavl_subscription_service.subscribe(
            api_key=api_key,
            name=form.cleaned_data["name"],
            url=form.cleaned_data["url"],
            update_interval=form.cleaned_data["update_interval"],
            subscription_id=subscription_id,
            dataset_ids=",".join(dataset_ids),
            bounding_box=form.cleaned_data["bounding_box"],
            operator_ref=form.cleaned_data["operator_ref"],
            vehicle_ref=form.cleaned_data["vehicle_ref"],
            line_ref=form.cleaned_data["line_ref"],
            producer_ref=form.cleaned_data["producer_ref"],
            origin_ref=form.cleaned_data["origin_ref"],
            destination_ref=form.cleaned_data["destination_ref"],
        )

        # then handle error responses appropriately by setting them in the error summary

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "api:buslocation-subscribe-success",
            args={},
            host=config.hosts.DATA_HOST,
        )


class AVLSubscriptionsSubscribeSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "api/avl_subscriptions_subscribe_success.html"


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
        try:
            Dataset.objects.get(pk=pk, dataset_type=DatasetType.AVL)
        except Dataset.DoesNotExist:
            msg = f"Datafeed {pk} does not exist."
            content = create_xml_error_response(msg, status.HTTP_404_NOT_FOUND)
            return Response(
                content, status=status.HTTP_404_NOT_FOUND, content_type="text/xml"
            )

        content, status_code = _get_consumer_api_response(url, request.query_params)
        return Response(content, status=status_code, content_type="text/xml")


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
