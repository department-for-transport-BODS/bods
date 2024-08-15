import logging
from http import HTTPStatus
from typing import Optional, Sequence

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException

from transit_odp.avl.client.interface import ICAVLService
from transit_odp.avl.dataclasses import Feed, ValidationTaskResult
from transit_odp.avl.enums import AVLFeedStatus


logger = logging.getLogger(__name__)


class CAVLService(ICAVLService):
    AVL_URL = settings.AVL_PRODUCER_API_BASE_URL
    headers = {"x-api-key": settings.AVL_PRODUCER_API_KEY}

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
        api_url = self.AVL_URL + "/subscriptions"

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

        return response.status_code == HTTPStatus.CREATED

    def delete_feed(self, feed_id: int) -> bool:
        api_url = self.AVL_URL + f"/subscriptions/{feed_id}"
        response = None

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
        api_url = self.AVL_URL + f"/subscriptions/{feed_id}"

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

        return response.status_code == HTTPStatus.NO_CONTENT

    def get_feed(self, feed_id: int) -> Feed:
        api_url = self.AVL_URL + f"/subscriptions/{feed_id}"

        try:
            response = requests.get(api_url, timeout=30, headers=self.headers)
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't fetch feed <id={feed_id}>. Response: {self._get_error_response(e)}"
            )
            return None

        if response.status_code == HTTPStatus.OK:
            feed = Feed(**response.json())
            api_status_map = {
                "live": AVLFeedStatus.live.value,
                "inactive": AVLFeedStatus.inactive.value,
                "error": AVLFeedStatus.error.value,
            }
            feed.status = api_status_map[feed.status]
            return feed

    def get_feeds(self) -> Sequence[Feed]:
        api_url = self.AVL_URL + "/subscriptions"

        try:
            response = requests.get(api_url, timeout=30, headers=self.headers)
            response.raise_for_status()
        except RequestException as e:
            logger.exception(
                f"[CAVL] Couldn't fetch feeds. Response: {self._get_error_response(e)}"
            )
            return []

        if response.status_code == HTTPStatus.OK:
            feeds = [Feed(**j) for j in response.json()]
            api_status_map = {
                "live": AVLFeedStatus.live.value,
                "inactive": AVLFeedStatus.inactive.value,
                "error": AVLFeedStatus.error.value,
            }
            for feed in feeds:
                feed.status = api_status_map[feed.status]
            return feeds

    def validate_feed(
        self, url: str, username: str, password: str, **kwargs
    ) -> Optional[ValidationTaskResult]:
        api_url = self.AVL_URL + "/feed/verify"

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
