import logging
import requests
from http import HTTPStatus
from datetime import date
from typing import Optional, List
from requests import HTTPError, RequestException, Timeout
from dataclasses import dataclass

from pydantic import Field, validator
from pydantic.main import BaseModel

from django.conf import settings
from django.core.exceptions import ValidationError
from transit_odp.otc.constants import API_TYPE_EP
from transit_odp.otc.ep.auth import EPAuthenticator


logger = logging.getLogger(__name__)


class EmptyResponseException(Exception):
    pass


retry_exceptions = (RequestException, EmptyResponseException)


class DataModel(BaseModel):
    service_number: str = Field(alias="routeNumber")
    registration_number: str = Field(alias="registrationNumber")
    variation_number: int = Field(alias="variationNumber")
    operator_name: str = Field(alias="operatorName")
    licence: str = Field(alias="licenceNumber")
    start_point: str = Field(alias="startPoint")
    finish_point: str = Field(alias="finishPoint")
    via: str = Field(alias="via")
    effective_date: date = Field(alias="effectiveDate")
    api_type: str = Field(default=API_TYPE_EP)
    service_type_description: str = Field(alias="busServiceTypeDescription")
    subsidies_description: str = Field(alias="subsidised")
    subsidies_details: str = Field(alias="subsidyDetail")
    atco_code: Optional[str] = Field(alias="registrationNumber")
    short_notice: bool = Field(alias="isShortNotice")
    received_date: date = Field(alias="receivedDate")
    end_date: date = Field(alias="endDate")

    @validator("registration_number")
    def trim_registration_number(cls, value, values):
        # Split the registration number by slash and take the first part and append the service_number
        reg_number_parts = value.split("/")
        if len(reg_number_parts) > 1:
            if "service_number" in values:
                return reg_number_parts[0] + "/" + values["service_number"]
            else:
                return reg_number_parts[0]
        else:
            return value

    @validator("atco_code", pre=True)
    def extract_atco_code(cls, value):
        # Extract the atco code after the first slash of registration_number
        reg_number_parts = value.split("/")
        if len(reg_number_parts) > 1:
            return reg_number_parts[1]
        else:
            return value


class APIResponse(BaseModel):
    Results: List[DataModel]


class EPClient:
    def __init__(self):
        self.ep_auth = EPAuthenticator()

    def _make_request(self, timeout: int = 30, **kwargs) -> APIResponse:
        """
        Send Request to EP API Endpoint
        Response will be returned in the JSON format
        """
        url = f"{settings.EP_API_URL}?active=true"
        headers = {
            "Authorization": f"Bearer {self.ep_auth.token}",
        }

        logger.info(f"headers: {headers}")
        try:
            response = requests.get(
                url=url,
                headers=headers,
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
            logger.warning(f"Empty Response, API return {HTTPStatus.NO_CONTENT}")
            return self.default_response()
        try:
            return APIResponse(**response.json())
        except ValidationError as exc:
            logger.error("Validation error in EP API response")
            logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")
        except ValueError as exc:
            logger.error("Validation error in EP API response")
            logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")
        return self.default_response()

    def default_response(self):
        """
        Create default return response for placeholder purpose
        """
        response = {"Results": []}
        return APIResponse(**response)

    def fetch_ep_services(self) -> APIResponse:
        """
        Fetch method for sending request to EP
        Return Pydentic model response
        """
        response = self._make_request()
        return response
