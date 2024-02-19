import logging
from http import HTTPStatus
from datetime import datetime, date

from typing import Optional, List
from pydantic import Field, field_validator, validator
from pydantic.main import BaseModel
from django.core.exceptions import ValidationError

import requests
from requests import HTTPError, RequestException, Timeout

from tenacity import retry, wait_exponential
from tenacity.retry import retry_if_exception_type
from tenacity.stop import stop_after_attempt

logger = logging.getLogger(__name__)

class EmptyResponseException(Exception):
    pass

retry_exceptions = (RequestException, EmptyResponseException)

class FieldModel(BaseModel):
    id:str
    name:str
    desc:str
    datatype:str

class DataModel(BaseModel):
    id: int
    registration_number: str = Field(alias="fullserialnumbe_trationrations")
    variation_number: int = Field(default=0)
    service_number: str = Field(alias="servicenumbers_icespt7a")
    start_point: str = Field(alias="startpoint_espt")
    finish_point: str = Field(alias="endpoint_sp")
    via: str = Field(alias="via_services_pt7atfu9e78z39yqc")
    effective_date: date  = Field(alias="proposedstartda_rviceslvicespt")
    api_type: str = Field(default="WECA")
    atco_code : Optional[str] = Field(alias="fullserialnumbe_trationrations")

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
    
    @validator("atco_code", pre=True)
    def extract_atco_code(cls, value):
        # Extract the first three digits after the first slash of registration_number
        reg_number_parts = value.split("/")
        if len(reg_number_parts) > 1 and len(reg_number_parts[1]) >= 3:
            return reg_number_parts[1][:3]
        else:
            return value


class APIResponse(BaseModel):
    fields:List[FieldModel]
    data:List[DataModel]

class WecaClient:
    @retry(
        retry=retry_if_exception_type(retry_exceptions),
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=1, max=60),
    )
    def _make_request(self, timeout: int = 30, **kwargs) -> APIResponse:
        url = "https://registrations.travelwest.info/agileBase/Public.ab"

        params = {
            "c": "pt7atfu9e78z39yqc",
            "t": "services_pt7atfu9e78z39yqc",
            "r": "copyofservicesl_vicespt7at01237",
            "get_report_json": "true",
            "json_format": "json",
            **kwargs
        }
        files = []
        headers = {"Authorization": "rwt4kzodylvyxad08d9jxdbdsp4djr94wq"}

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
            return APIResponse()
        try:
            return APIResponse(**response.json())
        except ValidationError as exc:
            logger.error("Validation error in WECA API response")
            logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")
        except ValueError as exc:
            logger.error("Validation error in WECA API response")
            logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")
        return APIResponse()

    def fetch_weca_services(self) -> APIResponse:
        response = self._make_request()
        return response
    