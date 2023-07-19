import logging
from datetime import datetime, timedelta
from functools import lru_cache
from http import HTTPStatus
from typing import Generator, List

import requests
from django.conf import settings
from django.utils import timezone
from pydantic import Field, validator
from pydantic.main import BaseModel
from requests import HTTPError, RequestException, Timeout
from tenacity import retry, wait_exponential
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt

from transit_odp.otc.client.auth import OTCAuthenticator
from transit_odp.otc.dataclasses import Registration, LocalAuthority

logger = logging.getLogger(__name__)
API_RETURN_LIMIT = 100


class EmptyResponseException(Exception):
    pass


retry_exceptions = (RequestException, EmptyResponseException)


class Page(BaseModel):
    current: int = 1
    total_count: int = Field(alias="totalCount", default=0)
    per_page: int = Field(alias="perPage", default=100)
    total_pages: int = Field(alias="totalPages", default=1)


class APIResponse(BaseModel):
    timestamp: datetime = Field(alias="timeStamp", default=datetime.now().isoformat())
    bus_search: List[Registration] = Field(alias="busSearch", default=[])
    bus_search_lta: List[LocalAuthority] = Field(alias="busSearch", default=[])
    page: Page = Page()

    @validator("timestamp", pre=True)
    def parse_timestamp(cls, v):
        if v:
            return datetime.strptime(v, "%d/%m/%Y %H:%M:%S")
        return


class OTCAPIClient:
    def __init__(self):
        self.otc_auth = OTCAuthenticator()

    @retry(
        retry=retry_if_exception_type(retry_exceptions),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=1, max=60),
    )
    def _make_request(self, timeout: int = 30, **kwargs) -> APIResponse:
        headers = {
            "x-api-key": settings.OTC_API_KEY,
            "Authorization": f"{self.otc_auth.token}",
        }
        defaults = {"limit": API_RETURN_LIMIT, "page": 1}
        params = {**defaults, **kwargs}
        try:
            response = requests.get(
                url=settings.OTC_API_URL,
                headers=headers,
                params=params,
                timeout=timeout,
            )
            response.raise_for_status()
        except Timeout as e:
            msg = f"Timeout Error: {e}"
            logger.exception(msg)
            raise

        except HTTPError as e:
            msg = f"HTTPError: {e}"
            logger.exception(msg)
            raise

        if response.status_code == HTTPStatus.NO_CONTENT:
            logger.warning(
                f"Empty Response, API return {HTTPStatus.NO_CONTENT}, "
                f"for params {params}"
            )
            return APIResponse()

        return APIResponse(**response.json())

    def get_latest_variations_since(self, when: datetime) -> List[Registration]:
        variations = []
        today = timezone.now().date()
        day_of_last_update = when.date()
        updated_on = day_of_last_update

        while updated_on < today:
            logger.info(
                f"Requesting all variations updated on {updated_on} from OTC API"
            )
            response = self._make_request(
                page=1, lastModifiedOn=updated_on.isoformat(), latestVariation=True
            )
            variations += response.bus_search

            for page in range(2, response.page.total_pages + 1):
                response = self._make_request(
                    page=page,
                    lastModifiedOn=updated_on.isoformat(),
                    latestVariation=True,
                )
                variations += response.bus_search

            updated_on += timedelta(days=1)

        return variations

    def get_latest_variations_by_registration_code(
        self, registration_codes: list
    ) -> List[Registration]:
        variations = []
        for registration_code in registration_codes:
            logger.info(
                f"Requesting latest variation for registration - {registration_code} from OTC API"
            )
            response = self._make_request(
                page=1, regNo=registration_code, latestVariation=True
            )
            variations += response.bus_search

            for page in range(2, response.page.total_pages + 1):
                response = self._make_request(
                    page=page,
                    regNo=registration_code,
                    latestVariation=True,
                )
                variations += response.bus_search

        return variations

    @lru_cache(maxsize=128, typed=False)
    def get_variations_by_registration_code_desc(
        self, registration_code: str
    ) -> List[Registration]:
        variations = []
        response = self._make_request(page=1, regNo=registration_code)
        if response:
            variations += response.bus_search

        for page in range(2, response.page.total_pages + 1):
            response = self._make_request(page=page, regNo=registration_code)
            if response:
                variations += response.bus_search

        return sorted(variations, key=lambda obj: obj.variation_number, reverse=True)

    def get_latest_variations_by_reg_status(
        self, registration_status: str
    ) -> Generator[Registration, None, None]:
        logger.info(
            f"Requesting all {registration_status} latest variations from OTC API - "
            f"page 1"
        )
        response = self._make_request(
            page=1, latestVariation=True, regStatus=registration_status
        )
        for record in response.bus_search:
            yield record

        total_pages = response.page.total_pages
        for page in range(2, total_pages + 1):
            msg = (
                f"Requesting all {registration_status} latest variations from "
                f"OTC API - page {page} of {total_pages}"
            )
            logger.info(msg)
            response = self._make_request(
                page=page, latestVariation=True, regStatus=registration_status
            )
            for record in response.bus_search:
                yield record

    def get_all_lta_names_latest_variations(self) -> List[LocalAuthority]:
        logger.info(f"Requesting all services from OTC API - " f"page 1")
        response = self._make_request(page=1, latestVariation=True)
        records = response.bus_search_lta

        total_pages = response.page.total_pages
        for page in range(2, total_pages + 1):
            msg = (
                f"Requesting all services - latest variations from "
                f"OTC API - page {page} of {total_pages}"
            )
            logger.info(msg)
            response = self._make_request(page=page, latestVariation=True)
            records += response.bus_search_lta

        return records
