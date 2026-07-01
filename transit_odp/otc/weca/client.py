import logging
import json
from datetime import datetime, date
from typing import Optional, List

from django.conf import settings
from django.core.exceptions import ValidationError
from pydantic import Field, validator
from pydantic.main import BaseModel

from transit_odp.otc.constants import API_TYPE_WECA
from transit_odp.common.utils.aws_common import get_s3_bucket_storage

logger = logging.getLogger(__name__)


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


class WECAData(BaseModel):
    fields: List[FieldModel]
    data: List[DataModel]


class WecaClient:
    def _make_request(self, timeout: int = 30, **kwargs) -> WECAData:
        """
        Send Request to WECA API Endpoint
        Response will be returned in the JSON format
        """

        s3_key = settings.WECA_DLZ_S3_KEY
        try:
            storage = get_s3_bucket_storage(settings.WECA_DLZ_S3_BUCKET)
            directories, files = storage.listdir("/raw/weca")
            print("Subdirectories:", directories)
            print("Files:", files)

            with storage.open(s3_key, "r") as f:
                response_json = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found in S3: {s3_key}")
            return self.default_response()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {s3_key}: {e}")
            return self.default_response()
        except Exception as e:
            logger.error(f"Error reading JSON from S3: {e}")
            return self.default_response()

        try:
            return WECAData(**response_json)
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
        return WECAData(**response)

    def fetch_weca_services(self) -> WECAData:
        """
        Fetch method for sending request to WECA
        Return Pydentic model response
        """
        response = self._make_request()
        return response
