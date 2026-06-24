import logging
import json
import boto3
from os import getenv
from datetime import datetime, date
from typing import Optional, List

from django.conf import settings
from django.core.exceptions import ValidationError
from pydantic import Field, validator
from pydantic.main import BaseModel

from transit_odp.otc.constants import API_TYPE_WECA

logger = logging.getLogger(__name__)
logger.setLevel(getenv("LOG_LEVEL") or "WARNING")


class FieldModel(BaseModel):
    id: str
    name: str
    desc: str
    datatype: str


class DataModel(BaseModel):
    id: int
    registration_number: str = Field(alias="fullserialnumbe_trationrations")
    variation_number: str = Field(alias="fullserialnumbe_trationrations")
    licence: str = Field(alias="fullserialnumbe_trationrations")
    service_number: str = Field(alias="servicenumbers_icespt7a")
    start_point: str = Field(alias="startpoint_espt")
    finish_point: str = Field(alias="endpoint_sp")
    via: str = Field(alias="via_services_pt7atfu9e78z39yqc")
    effective_date: date = Field(alias="proposedstartda_rviceslvicespt")
    api_type: str = Field(default=API_TYPE_WECA)
    atco_code: Optional[str] = Field(alias="fullserialnumbe_trationrations")

    @validator("effective_date", pre=True)
    def parse_effective_date(cls, value):
        # Fix for date issue identified here:
        # https://busopendataservice.atlassian.net/wiki/spaces/KBODS/pages/129040419/WECA+API+responses+sometimes+improperly+structured+causing+missing+or+incorrect+records+-+Fix+testing
        value = value.replace("Sept", "Sep")

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


class WecaClient:
    def _make_request(self, timeout: int = 30, **kwargs) -> APIResponse:
        """
        Send Request to WECA API Endpoint
        Response will be returned in the JSON format
        """

        s3_client = boto3.client("s3")
        try:
            logger.debug(f"Getting data from {settings.WECA_DLZ_S3_BUCKET}")
            logger.debug(f"Data key: {settings.WECA_DLZ_S3_KEY}")
            response_json = json.loads(
                s3_client.get_object(
                    Bucket=settings.WECA_DLZ_S3_BUCKET, Key=settings.WECA_DLZ_S3_KEY
                )["Body"]
                .read()
                .decode("utf-8")
            )
            logger.debug(f"Raw JSON:\n{response_json}")
        except Exception as e:
            logger.error(f"Error fetching WECA data from S3: {e}")
            return self.default_response()

        try:
            return APIResponse(**response_json)
        except ValidationError as exc:
            logger.error("Validation error in WECA API response")
            logger.error(f"Response JSON: {response_json}")
            logger.error(f"Validation Error: {exc}")
        except ValueError as exc:
            logger.error("Validation error in WECA API response")
            logger.error(f"Response JSON: {response_json}")
            logger.error(f"Validation Error: {exc}")
        return self.default_response()

    def default_response(self):
        """
        Create default return response for placeholder purpose
        """
        response = {"fields": [], "data": []}
        return APIResponse(**response)

    def fetch_weca_services(self) -> APIResponse:
        """
        Fetch method for sending request to WECA
        Return Pydentic model response
        """
        response = self._make_request()
        return response
