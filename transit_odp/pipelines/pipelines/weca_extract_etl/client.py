import requests
import re
from http import HTTPStatus
from datetime import datetime, date
from typing import Literal, Optional, List
from requests import HTTPError, Timeout

from django.conf import settings
from django.core.exceptions import ValidationError
from celery.utils.log import get_task_logger
from pydantic import Field, field_validator
from pydantic.main import BaseModel

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.otc.constants import API_TYPE_WECA


logger = get_task_logger(__name__)
logger = LoaderAdapter("WECAIngest", logger)


class FieldModel(BaseModel):
    id: str
    name: str
    desc: str
    datatype: str
    category: str


class ServicesModel(BaseModel):
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

    @field_validator("effective_date", mode="before")
    def parse_effective_date(cls, value):
        value = value.replace("Sept", "Sep")
        return datetime.strptime(value, "%d %b %Y")

    @field_validator("registration_number")
    def trim_registration_number(cls, value):
        # Split the registration number by slashes and take the first two parts
        parts = value.split("/")
        if len(parts) >= 2:
            return "/".join(parts[:2])
        else:
            return value

    @field_validator("variation_number")
    def trim_variation_number(cls, value):
        # Split the variation number by slashes and take the third part
        parts = value.split("/")
        if len(parts) == 3:
            return parts[2]
        else:
            return "0"

    @field_validator("licence")
    def extract_licence(cls, value):
        # Split the registration number by slashes and take the first parts
        parts = value.split("/")
        if len(parts) >= 1:
            return parts[0]
        else:
            return value

    @field_validator("atco_code", mode="before")
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


class RegistrationsModel(BaseModel):
    licence_number: str = Field(
        ...,
        min_length=1,
        json_schema_extra="PC7654321",
        alias="operatorlicence_istervices",
    )
    registration_number: str = Field(json_schema_extra="PD7654321/87654321", alias="serialnum_ervi")
    route_number: str = Field(..., json_schema_extra="2", alias="servicenumbers_icespt7a")
    route_description: str = Field(
        "",
        json_schema_extra="City Center - Suburb - Main Street",
        alias="routedescriptio_istervices",
    )
    variation_number: int = Field(..., json_schema_extra=1, alias="variation_ervi")
    start_point: str = Field(..., json_schema_extra="City Center", alias="startpoint_espt")
    finish_point: str = Field(..., json_schema_extra="Suburb", alias="endpoint_sp")
    via: str = Field(..., json_schema_extra="Main Street", alias="via_services_pt7atfu9e78z39yqc")
    subsidised: str = Field(..., json_schema_extra="Fully", alias="subsidised_tervic")
    subsidy_detail: str = Field(
        ...,
        json_schema_extra="Transport for Local Authority (LA)",
        alias="subsidisedby_stervice",
    )
    is_short_notice: bool = Field(..., json_schema_extra=False, alias="shortnotice_tervic")
    received_date: date = Field(..., json_schema_extra="01/01/2000", alias="receiveddate_stervice")
    granted_date: date = Field(..., json_schema_extra="01/02/2000", alias="granteddate_tervic")
    effective_date: date = Field(..., json_schema_extra="01/03/2000", alias="proposedstartda_istervices")
    end_date: date = Field(..., json_schema_extra="01/04/2000", alias="enddate_sp")
    operator_name: str = Field(..., json_schema_extra="Blue Sky Buses", alias="tenantid_sp")
    bus_service_type_id: str = Field(..., json_schema_extra="Standard", alias="servicetype_tervic")
    bus_service_type_description: str = Field(..., json_schema_extra="Normal Stopping", alias="typeofservice_stervice")
    traffic_area_id: str = Field(default="WECA", json_schema_extra="C")
    application_type: str = Field(..., json_schema_extra="New", alias="applicationtype_istervices")
    publication_text: Optional[str] = Field(
        None,
        json_schema_extra="Revised timetable to improve reliability",
        alias="publicationText",
    )
    other_details: Optional[str] = Field(None, json_schema_extra="", alias="otherDetails")

    @field_validator(
        "route_description",
        "subsidy_detail",
        "other_details",
        "publication_text",
        "finish_point",
        "start_point",
        "via",
        "operator_name",
        "application_type",
        "bus_service_type_description",
        mode="before",
    )
    def validate_route_description(cls, v):
        # Add cutation marks to the route description
        if isinstance(v, str) and len(v) > 0:
            return v.strip()
        return v

    @field_validator("received_date", "granted_date", "effective_date", "end_date", mode="before")
    def parse_date(cls, v):
        v = v.replace("Sept", "Sep")

        # if date in "02 Sep 2023" format change it to "02/09/2023"
        if re.match(r"\d{2} \w{3} \d{4}", v):
            v = datetime.strptime(v, "%d %b %Y").strftime("%d/%m/%Y")
        if v == "":
            return datetime.strptime("01/01/2100", "%d/%m/%Y")
        return datetime.strptime(v, "%d/%m/%Y")

    @field_validator("registration_number")
    def validate_registration_number(cls, v):
        """Validate the registration number format"""
        if not re.match(r"[a-zA-Z0-9]+/[a-zA-Z0-9]+", v):
            raise ValueError("Invalid registration number format")
        return v


class APIServiceResponse(BaseModel):
    fields: List[FieldModel]
    data: List[ServicesModel]


class APIRegistrationsResponse(BaseModel):
    fields: List[FieldModel]
    data: List[RegistrationsModel]


class WecaClient:
    def _make_request(
        self,
        dataset: Literal["services", "register"],
        param_c: str,
        param_t: str,
        param_r: str,
        timeout: int = 30,
        **kwargs,
    ) -> APIServiceResponse | APIRegistrationsResponse:
        """
        Send Request to WECA API Endpoint
        Response will be returned in the JSON format
        """

        params = {
            "c": param_c,
            "t": param_t,
            "r": param_r,
            "get_report_json": "true",
            "json_format": "json",
            **kwargs,
        }
        files = []
        headers = {
            "Authorization": settings.WECA_AUTH_TOKEN_SERVICES
            if dataset == "services"
            else settings.WECA_AUTH_TOKEN_REGISTRATIONS
        }
        logger.debug(f"Making request to WECA API with params: {params}")
        try:
            response = requests.post(
                url=self.url,
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

        logger.debug(f"API Response: {response.status_code}")
        if response.status_code == HTTPStatus.NO_CONTENT:
            logger.warning(f"Empty Response, API return {HTTPStatus.NO_CONTENT}, " f"for params {params}")
            return self.default_response(dataset)
        try:
            if dataset == "services":
                return APIServiceResponse(**response.json())
            return APIRegistrationsResponse(**response.json())
        except ValidationError as exc:
            logger.error("Validation error in WECA API response")
            # logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")
        except ValueError as exc:
            logger.error("Validation error in WECA API response")
            # # logger.error(f"Response JSON: {response.text}")
            logger.error(f"Validation Error: {exc}")
        return self.default_response(dataset)

    def default_response(self, dataset: Literal["services", "register"]):
        """
        Create default return response for placeholder purpose
        """

        response = {"fields": [], "data": []}
        if dataset == "services":
            return APIServiceResponse(**response)
        return APIRegistrationsResponse(**response)

    def fetch_weca_services(self) -> APIServiceResponse:
        """Fetch services data from the WECA API.

        Returns:
            APIServiceResponse: Latest services data.
        """
        logger.info("Making request to WECA API for services data")
        response = self._make_request(
            dataset="services",
            param_c=settings.WECA_PARAM_C_SERVICES,
            param_t=settings.WECA_PARAM_T_SERVICES,
            param_r=settings.WECA_PARAM_R_SERVICES,
        )
        return response

    def fetch_weca_registrations(self) -> APIRegistrationsResponse:
        """Fetch registrations data from the WECA API.

        Returns:
            APIRegistrationsResponse: Latest registrations data.
        """
        logger.info("Making request to WECA API for registrations data")
        response = self._make_request(
            dataset="register",
            param_c=settings.WECA_PARAM_C_REGISTRATIONS,
            param_t=settings.WECA_PARAM_T_REGISTRATIONS,
            param_r=settings.WECA_PARAM_R_REGISTRATIONS,
        )
        return response

    def __init__(self):
        logger.info("Initialized WECA API client")
        self.url = settings.WECA_API_URL
