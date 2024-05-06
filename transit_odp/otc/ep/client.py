import logging
import requests
from http import HTTPStatus
from datetime import datetime, date
from typing import Optional, List
from requests import HTTPError, RequestException, Timeout
from dataclasses import dataclass

from pydantic import Field, validator
from pydantic.main import BaseModel

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.cache import cache
from transit_odp.otc.constants import API_TYPE_EP

logger = logging.getLogger(__name__)


class EmptyResponseException(Exception):
    pass


retry_exceptions = (RequestException, EmptyResponseException)


class FieldModel(BaseModel):
    id: str
    name: str
    desc: str
    datatype: str


class DataModel(BaseModel):
    id: int
    registration_number: str = Field(alias="registrationNumber")
    variation_number: str = Field(alias="variationNumber")
    operator_name: str = Field(alias="operatorName")
    licence: str = Field(alias="licenceNumber")
    service_number: str = Field(alias="routeNumber")
    start_point: str = Field(alias="startPoint")
    finish_point: str = Field(alias="finishPoint")
    via: str = Field(alias="via")
    effective_date: date = Field(alias="effectiveDate")
    api_type: str = Field(default=API_TYPE_EP)
    atco_code: Optional[str] = Field(alias="fullserialnumbe_trationrations")
    service_type_description: str = Field(alias="busServiceTypeDescription")
    subsidies_description: str = Field(alias="subsidised")
    subsidies_details: str = Field(alias="subsidyDetail")


    @validator("effective_date", pre=True)
    def parse_effective_date(cls, value):
        return datetime.strptime(value, "%d %b %Y")

    @validator("registration_number")
    def trim_registration_number(cls, value):
        # Split the registration number by slashes and take the first two parts
        parts = value.split("/")
        if len(parts) >= 2:
            return "/".join(parts[:2])
        else:
            return value

    @validator("variation_number")
    def trim_variation_number(cls, value):
        # Split the variation number by slashes and take the third part
        parts = value.split("/")
        if len(parts) == 3:
            return parts[2]
        else:
            return "0"

    @validator("licence")
    def extract_licence(cls, value):
        # Split the registration number by slashes and take the first parts
        parts = value.split("/")
        if len(parts) >= 1:
            return parts[0]
        else:
            return value

    @validator("atco_code", pre=True)
    def extract_atco_code(cls, value):
        # Extract the first three digits after the first slash of registration_number
        reg_number_parts = value.split("/")
        if len(reg_number_parts) > 1:
            if len(reg_number_parts[1]) >= 3:
                return reg_number_parts[1][:3]
            else:
                return reg_number_parts[1]
        else:
            return value


class APIResponse(BaseModel):
    fields: List[FieldModel]
    data: List[DataModel]


class OTCAuthenticator:
    """
    Class responsible for providing Microsoft oauth2 Bearer token
    for sake of sending requests to the OTC API.
    OTC API requires 'Authorization' header to be added.
    {
        ...,
        "Authorization": <token>
    }
    """

    @property
    def token(self) -> str:
        """
        Fetch bearer token from Cache (Redis) or send request to generate new token.
        """
        return cache.get("ep-auth-bearer", None) or _get_token()


def _get_token() -> str:
    """
    Fetches Authorization Bearer token from MS.
    Updates cache with newly fetched auth token.

    Token cache timeout is calculated using the data received in response.

    expiry_time - 5mins (to invalidate cache while the first token is still active)
    """
    url = f"{settings.EP_AUTH_URL}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {
        "client_secret": settings.EP_CLIENT_SECRET,
        "client_id": settings.EP_CLIENT_ID,
        "grant_type": "client_credentials",
    }
    response = None
    try:
        response = requests.post(url=url, headers=headers, data=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        msg = f"Couldn't fetch Authorization token. {err}"
        logger.error(msg)
        logger.info(f"with credentials {body}")
        if response:
            logger.info(f"with content {response.content}")
        raise EPAuthorizationTokenException(msg)

    response = AuthResponse(**response.json())
    token_cache_timeout = response.expires_in
    cache.set("ep-auth-bearer", response.access_token, timeout=token_cache_timeout)
    return response.access_token


@dataclass(frozen=True)
class AuthResponse:
    expires_in: int
    access_token: str
    token_type: str


class EPAuthorizationTokenException(Exception):
    pass

class EPClient:
    def _make_request(self, timeout: int = 30, **kwargs) -> APIResponse:
        """
        Send Request to EP API Endpoint
        Response will be returned in the JSON format
        """
        url = f"{settings.EP_API_URL}?active=true"

        params = {
            "c": settings.EP_PARAM_C,
            "t": settings.EP_PARAM_T,
            "r": settings.EP_PARAM_R,
            "get_report_json": "true",
            "json_format": "json",
            **kwargs,
        }
        files = []
        headers = {"Authorization": settings.EP_AUTH_TOKEN}

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
        response = {"fields": [], "data": []}
        return APIResponse(**response)

    def fetch_ep_services(self) -> APIResponse:
        """
        Fetch method for sending request to EP
        Return Pydentic model response
        """
        response = self._make_request()
        return response
