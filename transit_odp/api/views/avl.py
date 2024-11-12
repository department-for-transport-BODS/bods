import logging
import uuid

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict
from django.views.generic import TemplateView
from requests import RequestException
from rest_framework import status, views, viewsets
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
from datetime import datetime

from transit_odp.api.renders import BinRenderer, ProtoBufRenderer, XMLRender
from transit_odp.api.utils.response_utils import create_xml_error_response
from transit_odp.common.tables import GovUkTable
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset

logger = logging.getLogger(__name__)

BODS_USER_API_KEY_PROPERTY = "api_key"


class AVLApiServiceView(LoginRequiredMixin, TemplateView):
    template_name = "api/avl_api_service.html"


class AVLOpenApiView(LoginRequiredMixin, TemplateView):
    template_name = "swagger_ui/avl.html"


def _format_query_params(query_params):
    formatted_query_params = []

    if "subscriptionId" in query_params:
        subscription_ids = ", ".join(query_params["subscriptionId"])
        formatted_query_params.append(f"Subscription Ids: {subscription_ids}")

    if "boundingBox" in query_params:
        bounding_box = ", ".join(map(str, query_params["boundingBox"]))
        formatted_query_params.append(f"Bounding Box: {bounding_box}")

    if "operatorRef" in query_params:
        operator_ref = ", ".join(query_params["operatorRef"])
        formatted_query_params.append(f"Operator Ref: {operator_ref}")

    if "lineRef" in query_params:
        line_ref = query_params["lineRef"]
        formatted_query_params.append(f"Line Ref: {line_ref}")

    if "producerRef" in query_params:
        producer_ref = query_params["producerRef"]
        formatted_query_params.append(f"Producer Ref: {producer_ref}")

    if "vehicleRef" in query_params:
        vehicle_ref = query_params["vehicleRef"]
        formatted_query_params.append(f"Vehicle Ref: {vehicle_ref}")

    if "originRef" in query_params:
        origin_ref = query_params["originRef"]
        formatted_query_params.append(f"Origin Ref: {origin_ref}")

    if "destinationRef" in query_params:
        destination_ref = query_params["destinationRef"]
        formatted_query_params.append(f"Destination Ref: {destination_ref}")

    return "; \n ".join(formatted_query_params)


class AVLManageSubscriptionsView(LoginRequiredMixin, TemplateView):
    template_name = "api/avl_subscriptions_manage.html"
    cavl_subscription_service = CAVLSubscriptionService()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_key = Token.objects.get_or_create(user=self.request.user)[0].key

        content = None
        try:
            content = self.cavl_subscription_service.get_subscriptions(api_key=api_key)
        except RequestException:
            context["error"] = "true"

        if content is None:
            context["error"] = "true"

        else:
            status_dict = {
                "live": "Active",
                "error": "Error",
                "inactive": "Inactive",
            }

            formatted_subscriptions = [
                {
                    "name": subscription["name"],
                    "data_filters": _format_query_params(subscription["queryParams"]),
                    "status": status_dict[subscription["status"]],
                    "set_up_date": datetime.strptime(
                        subscription["requestTimestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                    if subscription["requestTimestamp"]
                    else "",
                }
                for subscription in content
            ]

            context["active_subscriptions"] = [
                sub
                for sub in formatted_subscriptions
                if sub["status"] in ["Active", "Error"]
            ]
            context["inactive_subscriptions"] = [
                sub for sub in formatted_subscriptions if sub["status"] in ["Inactive"]
            ]

        return context


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
        data_feed_ids = [
            form.cleaned_data["data_feed_id_1"],
            form.cleaned_data["data_feed_id_2"],
            form.cleaned_data["data_feed_id_3"],
            form.cleaned_data["data_feed_id_4"],
            form.cleaned_data["data_feed_id_5"],
        ]
        data_feed_ids_set = set(
            [data_feed_id for data_feed_id in data_feed_ids if data_feed_id]
        )

        try:
            self.cavl_subscription_service.subscribe(
                api_key=api_key,
                name=form.cleaned_data["name"],
                url=form.cleaned_data["url"],
                update_interval=f"PT{form.cleaned_data['update_interval']}S",
                subscription_id=subscription_id,
                data_feed_ids=",".join(data_feed_ids_set),
                bounding_box=form.cleaned_data["bounding_box"],
                operator_ref=form.cleaned_data["operator_ref"],
                vehicle_ref=form.cleaned_data["vehicle_ref"],
                line_ref=form.cleaned_data["line_ref"],
                producer_ref=form.cleaned_data["producer_ref"],
                origin_ref=form.cleaned_data["origin_ref"],
                destination_ref=form.cleaned_data["destination_ref"],
            )
        except RequestException as e:
            status_code = e.response.status_code

            error_messages = e.response.json().get("errors", [])
            error_message = (
                _(error_messages[0])
                if error_messages
                else "The service is unavailable, try again later"
            )

            match status_code:
                case 400:
                    for message in e.errors:
                        form.add_error(None, _(message))
                case 404:
                    # The following code is used to extract the correct data_feed ID from the server error message
                    # so that the appropriate field in the form can be highlighted with a UI error message
                    field_name = None
                    subscription_id_not_found = error_message.split(":")[-1].strip()

                    if subscription_id_not_found in data_feed_ids:
                        index = data_feed_ids.index(subscription_id_not_found)
                        field_name = f"data_feed_id_{index + 1}"
                    else:
                        field_name = None

                    form.add_error(
                        field_name, f"ID not found: {subscription_id_not_found}"
                    )
                case 409:
                    form.add_error(None, error_message)
                case 429:
                    form.add_error(None, error_message)
                case 503:
                    form.add_error(None, error_message)
                case _:
                    form.add_error(None, error_message)

            return self.form_invalid(form)

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


class AVLConsumerSubscriptionsApiViewSet(viewsets.ViewSet):
    """APIViewSet for managing AVL consumer subscriptions."""

    cavl_subscription_service = CAVLSubscriptionService()

    permission_classes = (IsAuthenticated,)

    def create(self, request, format=None):
        """Subscribe AVL consumer subscription"""
        api_key = (
            request.user.auth_token.key
            if request.user.is_authenticated
            else request.query_params.get("api_key")
        )
        status_code = status.HTTP_200_OK
        content = ""
        subscription_id = uuid.uuid4()

        try:
            self.cavl_subscription_service.subscribe(
                api_key=api_key,
                name=request.data.get("name"),
                url=request.data.get("url"),
                update_interval=request.data.get("updateInterval"),
                subscription_id=subscription_id,
                data_feed_ids=",".join(request.data.get("dataFeedIds", [])),
                bounding_box=",".join(map(str, request.data.get("bounding_box", []))),
                operator_ref=",".join(request.data.get("operatorRef", [])),
                vehicle_ref=request.data.get("vehicleRef"),
                line_ref=request.data.get("lineRef"),
                producer_ref=request.data.get("producerRef"),
                origin_ref=request.data.get("originRef"),
                destination_ref=request.data.get("destinationRef"),
            )
            content = dict(subscriptionId=subscription_id)
        except RequestException as e:
            status_code = e.response.status_code
            content = e.response.content

        return Response(content, status=status_code)

    def list(self, request, format=None):
        """Get AVL consumer subscription details"""
        api_key = (
            request.user.auth_token.key
            if request.user.is_authenticated
            else request.query_params.get("api_key")
        )
        status_code = status.HTTP_200_OK
        content = ""

        try:
            content = self.cavl_subscription_service.get_subscriptions(api_key=api_key)
        except RequestException as e:
            status_code = e.response.status_code
            content = e.response.content

        return Response(content, status=status_code)


class AVLConsumerSubscriptionApiViewSet(viewsets.ViewSet):
    """APIViewSet for managing AVL consumer subscriptions."""

    cavl_subscription_service = CAVLSubscriptionService()

    permission_classes = (IsAuthenticated,)

    def destroy(self, request, subscription_id=-1, format=None):
        """Unsubscribe AVL consumer subscription"""
        api_key = (
            request.user.auth_token.key
            if request.user.is_authenticated
            else request.query_params.get("api_key")
        )
        status_code = status.HTTP_200_OK
        content = ""

        try:
            content = self.cavl_subscription_service.unsubscribe(
                api_key=api_key, subscription_id=subscription_id
            )
        except RequestException as e:
            status_code = e.response.status_code
            content = e.response.content

        return Response(content, status=status_code)

    def list(self, request, subscription_id=-1, format=None):
        """Get AVL consumer subscription details"""
        api_key = (
            request.user.auth_token.key
            if request.user.is_authenticated
            else request.query_params.get("api_key")
        )
        status_code = status.HTTP_200_OK
        content = ""

        try:
            content = self.cavl_subscription_service.get_subscription(
                api_key=api_key, subscription_id=subscription_id
            )
        except RequestException as e:
            status_code = e.response.status_code
            content = e.response.content

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
    params.pop(BODS_USER_API_KEY_PROPERTY, None)

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
    params.pop(BODS_USER_API_KEY_PROPERTY, None)

    ALLOWED_PARAMETERS = (
        "boundingBox",
        "destinationRef",
        "lineRef",
        "operatorRef",
        "originRef",
        "producerRef",
        "vehicleRef",
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
