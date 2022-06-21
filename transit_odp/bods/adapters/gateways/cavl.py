import logging
from http import HTTPStatus
from typing import Optional, Sequence

import requests
from django.conf import settings
from requests.exceptions import RequestException

from transit_odp.avl.clients.cavl import Feed, ValidationTaskResult
from transit_odp.bods.interfaces.gateways import ICAVLService

logger = logging.getLogger(__name__)


class CAVLService(ICAVLService):
    CAVL_URL = settings.CAVL_URL

    def register_feed(
        self,
        feed_id: int,
        publisher_id: int,
        url: str,
        username: str,
        password: str,
    ) -> bool:
        api_url = self.CAVL_URL + "/feed"
        post = {
            "id": feed_id,
            "publisherId": publisher_id,
            "url": url,
            "username": username,
            "password": password,
        }

        try:
            response = requests.post(api_url, json=post, timeout=30)
        except RequestException:
            return False

        return response.status_code == HTTPStatus.CREATED

    def delete_feed(self, feed_id: int) -> bool:
        api_url = self.CAVL_URL + f"/feed/{feed_id}"
        try:
            response = requests.delete(api_url, timeout=30)
        except RequestException:
            return False

        return response.status_code == HTTPStatus.NO_CONTENT

    def update_feed(self, feed_id: int, url: str, username: str, password: str) -> bool:
        api_url = self.CAVL_URL + f"/feed/{feed_id}"

        body = {"url": url, "username": username, "password": password}

        try:
            response = requests.post(api_url, json=body, timeout=30)
        except RequestException:
            return False

        return response.status_code == HTTPStatus.NO_CONTENT

    def get_feed(self, feed_id: int) -> Optional[Feed]:
        api_url = self.CAVL_URL + f"/feed/{feed_id}"
        try:
            response = requests.get(api_url, timeout=30)
        except RequestException as exc:
            message = f"Exception {exc} raise when calling FeedApi->get_feed"
            logger.exception(message)
            return None
        if response.status_code == HTTPStatus.OK:
            return Feed(**response.json())

    def get_feeds(self) -> Sequence[Feed]:
        api_url = self.CAVL_URL + "/feed"
        try:
            response = requests.get(api_url, timeout=30)
        except RequestException as exc:
            message = f"Exception {exc} raise when calling FeedApi->get_feed"
            logger.exception(message)
            return []
        if response.status_code == HTTPStatus.OK:
            return [Feed(**j) for j in response.json()]

    def validate_feed(
        self, url: str, username: str, password: str, **kwargs
    ) -> Optional[ValidationTaskResult]:
        api_url = self.CAVL_URL + "/validate"

        body = {
            "url": url,
            "username": username,
            "password": password,
            "status": None,
            "created": None,
        }

        try:
            response = requests.post(api_url, json=body, timeout=30)
        except RequestException as exc:
            message = f"Exception {exc} raise when calling FeedApi->get_feed"
            logger.exception(message)
            raise
        if response.status_code == HTTPStatus.OK:
            return ValidationTaskResult(**response.json())
        return None
