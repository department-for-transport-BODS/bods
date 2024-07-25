import logging
from http import HTTPStatus
from typing import Optional, Sequence

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException, ConnectionError

from transit_odp.avl.client.interface import ICAVLService
from transit_odp.avl.dataclasses import Feed, ValidationTaskResult


logger = logging.getLogger(__name__)


class CAVLService(ICAVLService):
    CAVL_URL = settings.CAVL_URL
    AVL_URL = settings.AVL_PRODUCER_API_BASE_URL
    headers = {"x-api-key": settings.AVL_PRODUCER_API_KEY}

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
            print("Subscribing to AVL service")
            response = requests.post(
                api_url, json=post, timeout=30, headers=self.headers
            )
            response.raise_for_status()
        except RequestException:
            logger.exception(f"[CAVL] Couldn't register feed <id={feed_id}>")
            raise

        return response.status_code == HTTPStatus.CREATED

    def delete_feed(self, feed_id: int) -> bool:
        api_url = self.CAVL_URL + f"/feed/{feed_id}"
        response = None

        try:
            response = requests.delete(api_url, timeout=30)
            response.raise_for_status()
        except ConnectionError:
            logger.exception(f"[CAVL] Couldn't delete feed <id={feed_id}>")
            return False
        except RequestException:
            if response is not None and response.status_code == HTTPStatus.NOT_FOUND:
                logger.error(
                    f"[CAVL] Dataset {feed_id} => Does not exist in CAVL Service."
                )
            else:
                logger.exception(f"[CAVL] Couldn't delete feed <id={feed_id}>")
            return False

        return response.status_code == HTTPStatus.NO_CONTENT

    def update_feed(self, feed_id: int, url: str, username: str, password: str) -> bool:
        api_url = self.CAVL_URL + f"/feed/{feed_id}"

        body = {"url": url, "username": username, "password": password}

        try:
            response = requests.post(api_url, json=body, timeout=30)
            response.raise_for_status()
        except RequestException:
            logger.exception(f"[CAVL] Couldn't update feed <id={feed_id}>")
            return False

        return response.status_code == HTTPStatus.NO_CONTENT

    def get_feed(self, feed_id: int) -> Optional[Feed]:
        api_url = self.CAVL_URL + f"/feed/{feed_id}"

        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
        except RequestException:
            logger.exception(f"[CAVL] Couldn't fetch feed <id={feed_id}>")
            return None

        if response.status_code == HTTPStatus.OK:
            return Feed(**response.json())

    def get_feeds(self) -> Sequence[Feed]:
        api_url = self.CAVL_URL + "/feed"

        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
        except RequestException:
            logger.exception("[CAVL] Couldn't fetch feeds")
            return []

        if response.status_code == HTTPStatus.OK:
            return [Feed(**j) for j in response.json()]

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
        except RequestException:
            logger.exception(f"[CAVL] Couldn't validate feed <url={url}>")
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
