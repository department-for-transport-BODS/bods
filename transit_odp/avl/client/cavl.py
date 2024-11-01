from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from http import HTTPStatus
from typing import Optional, Sequence
import uuid

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException

from transit_odp.avl.client.interface import ICAVLService, ICAVLSubscriptionService
from transit_odp.avl.dataclasses import Feed, ValidationTaskResult


logger = logging.getLogger(__name__)


class CAVLService(ICAVLService):
    AVL_PRODUCER_URL = settings.AVL_PRODUCER_API_BASE_URL
    headers = {"x-api-key": settings.AVL_PRODUCER_API_KEY}

    @staticmethod
    def _get_error_response(exception: RequestException) -> str:
        return (
            exception.response.json()
            if hasattr(exception.response, "json")
            else "(empty)"
        )

    def register_feed(
        self,
        feed_id: int,
        publisher_id: int,
        url: str,
        username: str,
        password: str,
        description: str,
        short_description: str,
    ) -> bool:
        api_url = self.AVL_PRODUCER_URL + "/subscriptions"

        post = {
            "subscriptionId": str(feed_id),
            "publisherId": str(publisher_id),
            "dataProducerEndpoint": url,
            "username": username,
            "password": password,
            "description": description,
            "shortDescription": short_description,
        }

        try:
            response = requests.post(
                api_url, json=post, timeout=30, headers=self.headers
            )
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't register feed <id={feed_id}>. Response: {self._get_error_response(e)}"
            )
            raise

    def delete_feed(self, feed_id: int) -> bool:
        api_url = self.AVL_PRODUCER_URL + f"/subscriptions/{feed_id}"

        try:
            response = requests.delete(api_url, timeout=30, headers=self.headers)
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't delete feed <id={feed_id}>. Response: {self._get_error_response(e)}"
            )
            raise

    def update_feed(
        self,
        feed_id: int,
        url: str,
        username: str,
        password: str,
        description: str,
        short_description: str,
    ) -> bool:
        api_url = self.AVL_PRODUCER_URL + f"/subscriptions/{feed_id}"

        body = {
            "dataProducerEndpoint": url,
            "username": username,
            "password": password,
            "description": description,
            "shortDescription": short_description,
        }

        try:
            response = requests.put(
                api_url, json=body, timeout=30, headers=self.headers
            )
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't update feed <id={feed_id}>. Response: {self._get_error_response(e)}"
            )
            raise

    def get_feed(self, feed_id: int) -> Feed:
        api_url = self.AVL_PRODUCER_URL + f"/subscriptions/{feed_id}"

        try:
            response = requests.get(api_url, timeout=30, headers=self.headers)
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't fetch feed <id={feed_id}>. Response: {self._get_error_response(e)}"
            )
            raise

        if response.status_code == HTTPStatus.OK:
            return Feed(**response.json())

    def get_feeds(self) -> Sequence[Feed]:
        api_url = self.AVL_PRODUCER_URL + "/subscriptions"

        try:
            response = requests.get(api_url, timeout=30, headers=self.headers)
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't fetch feeds. Response: {self._get_error_response(e)}"
            )
            raise

        if response.status_code == HTTPStatus.OK:
            return [Feed(**j) for j in response.json()]

    def validate_feed(
        self, url: str, username: str, password: str, **kwargs
    ) -> Optional[ValidationTaskResult]:
        api_url = self.AVL_PRODUCER_URL + "/feed/verify"

        body = {
            "url": url,
            "username": username,
            "password": password,
        }

        try:
            response = requests.put(
                api_url, json=body, timeout=30, headers=self.headers
            )
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't validate feed <url={url}>. Response: {self._get_error_response(e)}"
            )
            raise

        if response.status_code == HTTPStatus.OK:
            content = response.json()
            siri_version = content["siriVersion"]

            return ValidationTaskResult(
                status="FEED_VALID",
                url=url,
                username=username,
                password=password,
                created=timezone.now(),
                version=siri_version,
            )


class CAVLSubscriptionService(ICAVLSubscriptionService):
    AVL_CONSUMER_URL = settings.AVL_CONSUMER_API_BASE_URL

    @staticmethod
    def _get_error_response(exception: RequestException) -> str:
        return (
            exception.response.json()
            if hasattr(exception.response, "json")
            else "(empty)"
        )

    def subscribe(
        self,
        api_key: str,
        name: str,
        url: str,
        update_interval: int,
        subscription_id: str,
        dataset_ids: str,
        bounding_box: str,
        operator_ref: str,
        vehicle_ref: str,
        line_ref: str,
        producer_ref: str,
        origin_ref: str,
        destination_ref: str,
    ) -> None:
        api_url = f"{self.AVL_CONSUMER_URL}/v1/siri-vm/subscriptions?name={name}&subscriptionId={dataset_ids}"

        if bounding_box:
            api_url += "&boundingBox=" + bounding_box

        if operator_ref:
            api_url += "&operatorRef=" + operator_ref

        if vehicle_ref:
            api_url += "&vehicleRef=" + vehicle_ref

        if line_ref:
            api_url += "&lineRef=" + line_ref

        if producer_ref:
            api_url += "&producerRef=" + producer_ref

        if origin_ref:
            api_url += "&originRef=" + origin_ref

        if destination_ref:
            api_url += "&destinationRef=" + destination_ref

        current_datetime = datetime.now()
        request_timestamp = current_datetime.isoformat() + "Z"
        initial_termination_timestamp = (
            current_datetime + relativedelta(years=50)
        ).isoformat() + "Z"
        message_identifier = uuid.uuid4()

        headers = {
            "Content-Type": "application/xml",
            "x-api-key": api_key,
        }

        xml = f"""
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Siri version="2.0" xmlns="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.siri.org.uk/siri http://www.siri.org.uk/schema/2.0/xsd/siri.xsd">
  <SubscriptionRequest>
    <RequestTimestamp>{request_timestamp}</RequestTimestamp>
    <ConsumerAddress>{url}</ConsumerAddress>
    <RequestorRef>BODS</RequestorRef>
    <MessageIdentifier>{message_identifier}</MessageIdentifier>
    <SubscriptionContext>
      <HeartbeatInterval>PT30S</HeartbeatInterval>
    </SubscriptionContext>
    <VehicleMonitoringSubscriptionRequest>
      <SubscriptionIdentifier>{subscription_id}</SubscriptionIdentifier>
      <InitialTerminationTime>{initial_termination_timestamp}</InitialTerminationTime>
      <VehicleMonitoringRequest version="2.0">
        <RequestTimestamp>{request_timestamp}</RequestTimestamp>
        <VehicleMonitoringDetailLevel>normal</VehicleMonitoringDetailLevel>
      </VehicleMonitoringRequest>
    <UpdateInterval>PT{update_interval}S</UpdateInterval>
    </VehicleMonitoringSubscriptionRequest>
  </SubscriptionRequest>
</Siri>
"""

        try:
            response = requests.post(api_url, data=xml, timeout=30, headers=headers)
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't create AVL consumer subscription <id={subscription_id}> <name={name}>. Response: {self._get_error_response(e)}"
            )

            raise
