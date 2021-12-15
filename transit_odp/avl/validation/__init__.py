from http import HTTPStatus
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from requests.exceptions import RequestException

from transit_odp.avl.validation.constants import DEFAULT_TIMEOUT
from transit_odp.avl.validation.models import (
    SchemaValidationResponse,
    ValidationResponse,
)

GET = "GET"


def get_validation_client():
    return ValidationClient(url=settings.CAVL_VALIDATION_URL)


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

    def validate(
        self, feed_id: int, sample_size: int = 50
    ) -> Optional[ValidationResponse]:
        """
        Calls the AVL validate endpoint and returns the result of a validation.

        Args:
            feed_id: The data feed id to validate.
            sample_size: The number of packets to use in the validation.

        Returns:
            ValidationResponse or None
        """
        endpoint = self.url + f"/validate/{feed_id}"
        params = {"sample_size": sample_size}
        data = self._make_request(GET, endpoint, params=params, timeout=DEFAULT_TIMEOUT)

        if data is not None:
            return ValidationResponse(**data)
        else:
            return None

    def schema(self, feed_id: int) -> SchemaValidationResponse:
        """
        Called the AVL schema validate endpoint and returns the result of a SIRI
        VM 2.0 schema validation.

        Args:
            feed_id: The id of the data feed to validate.

        Returns:
            SchemaValidationResponse or None
        """
        endpoint = self.url + f"/schema/{feed_id}"
        data = self._make_request(GET, endpoint, timeout=DEFAULT_TIMEOUT)

        if data is not None:
            return SchemaValidationResponse(**data)
        else:
            # We just want to return a rubbish response and signal to the caller
            # that it's rubbish using a 0 timestamp and empty errors list
            return SchemaValidationResponse(
                feed_id=feed_id, is_valid=True, timestamp=0, errors=[]
            )
