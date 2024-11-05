import logging
import requests
from http import HTTPStatus
from datetime import datetime
from typing import Optional, List, Union
from requests import HTTPError, RequestException, Timeout

from django.conf import settings
from django.core.exceptions import ValidationError

from pydantic.main import BaseModel

logger = logging.getLogger(__name__)


class EmptyResponseException(Exception):
    pass


retry_exceptions = (RequestException, EmptyResponseException)


class LineStatus(BaseModel):
    lineName: Union[str, int]
    lastRecordedAtTime: datetime
    operatorNoc: str


class AVLLineLevelStatus(BaseModel):
    avlLineLevelStatus: Optional[List[LineStatus]]


class APIResponse(BaseModel):
    data: AVLLineLevelStatus


class AbodsClient:
    def _make_request(self, timeout: int = 30, **kwargs) -> APIResponse:
        """
        Send Request to Abods API Endpoint
        Response will be returned in the JSON format
        """
        url = settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL

        params = {
            "query": "query ExampleQuery { avlLineLevelStatus { operatorNoc lineName lastRecordedAtTime } }",
            **kwargs,
        }
        files = []
        headers = {"Authorization": f"Bearer {settings.ABODS_AVL_AUTH_TOKEN}"}

        try:
            response = requests.post(
                url=url,
                headers=headers,
                params=params,
                files=files,
                timeout=timeout,
            )
            response.raise_for_status()
        except Timeout as e:
            msg = f"Timeout Error: {e}"
            logger.exception(msg)
            return self.default_response()

        except HTTPError as e:
            msg = f"HTTPError: {e}"
            logger.exception(msg)
            return self.default_response()
        except Exception as exc:
            logger.error("Unexpected error in ABODS API response")
            logger.exception(exc)
            return self.default_response()

        if response.status_code == HTTPStatus.NO_CONTENT:
            logger.warning(
                f"Empty Response, API return {HTTPStatus.NO_CONTENT}, "
                f"for params {params}"
            )
            return self.default_response()
        try:
            return APIResponse(**response.json())
        except ValidationError as exc:
            logger.error("Validation error in ABODS API response")
            logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")
        except ValueError as exc:
            logger.error("Validation error in ABODS API response")
            logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")

        return self.default_response()

    def default_response(self):
        """
        Create default return response for placeholder purpose
        """
        response = {"data": {"avlLineLevelStatus": []}}
        return APIResponse(**response)

    def fetch_line_details(self) -> APIResponse:
        """
        Fetch method for sending request to ABODS
        Return Pydentic model response
        """
        response = self._make_request()
        return response


class AbodsRegistery:
    def __init__(self):
        self._client = AbodsClient()
        self.lines = []
        self.data = None

    def records(self):
        self.fetch_records()
        self.normailze()
        self.remove_duplicate()
        return self.lines

    def normailze(self):
        logger.info("ABODSRegistery: Nomalizing line details")
        for line_details in self.data.avlLineLevelStatus:
            self.lines.append(f"{line_details.lineName}__{line_details.operatorNoc}")
        logger.info(f"ABODSRegistery: Total {len(self.lines)} lines normalised")

    def remove_duplicate(self):
        self.lines = list(set(self.lines))
        logger.info(f"ABODSRegistery: Total {len(self.lines)} unique lines left")

    def fetch_records(self) -> APIResponse:
        """
        Fetch the records from the abods lines
        """
        logger.info("ABODSRegistery: Fetching lines from ABODS")
        response = self._client.fetch_line_details()
        self.data = response.data
        logger.info(
            "ABODSRegistery: Total Lines found {}".format(
                len(self.data.avlLineLevelStatus)
            )
        )
        return response
