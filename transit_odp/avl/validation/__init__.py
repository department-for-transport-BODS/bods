from http import HTTPStatus
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from requests.exceptions import RequestException

from transit_odp.avl.validation.constants import DEFAULT_TIMEOUT
from transit_odp.avl.validation.models import (
    ValidationResponse,
)

GET = "GET"


def get_validation_client():
    return ValidationClient(url=settings.AVL_PRODUCER_API_BASE_URL)


class ValidationClient:
    def __init__(self, url: str):
        if url.endswith("/"):
            self.url = url[0:-1]
        else:
            self.url = url

    def _make_request(
        self, method: str, url: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        try:
            response = requests.request(method=method, url=url, **kwargs)
        except RequestException:
            return None

        if response.status_code == HTTPStatus.OK:
            data = response.json()
            return data
        else:
            return None

    def validate(self, feed_id: int) -> Optional[ValidationResponse]:
        """
        Calls the validate-profile endpoint for a given subscription. It will return the validation errors collated
        within the last 24 hours for a given data producer. Validation follows the rules defined in the SIRI 2.0 schema

        Args:
            feed_id: The data feed id to validate.

        Returns:
            ValidationResponse or None
        """
        endpoint = self.url + f"/subscriptions/{feed_id}/validate-profile"

        print(endpoint)
        headers = {"x-api-key": settings.AVL_PRODUCER_API_KEY}
        data = self._make_request(
            GET, endpoint, timeout=DEFAULT_TIMEOUT, headers=headers
        )

        print("data", data)

        if data is not None:
            try:
                return ValidationResponse(**data)
            except ValueError as e:
                print(e)

        else:
            return None
