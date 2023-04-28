from datetime import date, datetime
from typing import Optional, List

from django.utils.timezone import make_aware
from pydantic import Field, validator
from pydantic.main import BaseModel


class Registration(BaseModel):
    class Config:
        allow_population_by_field_name = True

    registration_number: str = Field(alias="registrationNumber")
    variation_number: int = Field(alias="variationNumber")
    service_number: Optional[str] = Field(alias="serviceNumber")
    current_traffic_area: Optional[str] = Field(alias="trafficAreaId")
    licence_number: Optional[str] = Field(alias="licenceNumber")
    discs_in_possession: Optional[int] = Field(alias="discsInPossession")
    authdiscs: Optional[int] = Field(alias="authDiscs")
    licence_granted_date: Optional[date] = Field(alias="grantedDate")
    licence_expiry_date: Optional[date] = Field(alias="expiryDate")
    description: Optional[str] = Field(alias="licenceType")
    operator_id: int = Field(alias="operatorId")
    operator_name: Optional[str] = Field(alias="operatorName")
    trading_name: Optional[str] = Field(alias="tradingName")
    address: str = Field(alias="contactAddress1")
    start_point: Optional[str] = Field(alias="startPoint")
    finish_point: Optional[str] = Field(alias="finishPoint")
    via: Optional[str] = Field(alias="via")
    effective_date: Optional[date] = Field(alias="effectiveDate")
    received_date: Optional[date] = Field(alias="receivedDate")
    end_date: Optional[date] = Field(alias="endDate")
    service_type_other_details: Optional[str] = Field(alias="otherDetails")
    licence_status: Optional[str] = Field(alias="licenceStatus")
    registration_status: Optional[str] = Field(alias="registrationStatus")
    public_text: Optional[str] = Field(alias="publicationText")
    service_type_description: Optional[str] = Field(alias="busServiceTypeDescription")
    short_notice: Optional[bool] = Field(alias="isShortNotice")
    subsidies_description: Optional[str] = Field(alias="subsidised")
    subsidies_details: Optional[str] = Field(alias="subsidyDetail")
    auth_description: Optional[str] = Field(alias="localAuthorities")
    tao_covered_by_area: Optional[str] = Field(alias="taoCoveredByArea")
    registration_code: Optional[int] = Field(alias="registrationCode")
    last_modified: Optional[datetime] = Field(alias="lastModifiedOn")
    local_authorities: Optional[str] = Field(alias="localAuthorities")

    @validator(
        "licence_granted_date",
        "licence_expiry_date",
        "effective_date",
        "received_date",
        "end_date",
        pre=True,
    )
    def parse_date(cls, v):
        if v:
            return datetime.strptime(v, "%d/%m/%Y").date()
        return

    @validator("last_modified", pre=True)
    def parse_datetime(cls, v):
        if v:
            last_modified = datetime.strptime(v, "%d/%m/%Y %H:%M:%S")
            last_modified = make_aware(last_modified)
            return last_modified
        return

    @validator(
        "variation_number",
        "discs_in_possession",
        "authdiscs",
        "operator_id",
        "end_date",
        "short_notice",
        "registration_code",
        pre=True,
    )
    def empty_to_none(cls, v):
        if v == "":
            return
        return v

    @validator(
        "subsidies_description",
        "subsidies_details",
        "public_text",
        "via",
        "service_type_other_details",
        "service_number",
        "current_traffic_area",
        "start_point",
        "finish_point",
        "description",
        "registration_status",
        "service_type_description",
        pre=True,
    )
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v

    @validator("registration_number", "licence_number")
    def validate_not_empty(cls, v):
        # Note all strings are empty by default, these are the only ones that
        # cannot be optional
        if v.lower() in EMPTY_VALUES:
            raise ValueError(f"{v} is an empty value but it is required")
        return v


class Licence(BaseModel):
    class Config:
        allow_population_by_field_name = True

    number: str = Field(alias="licence_number")
    status: Optional[str] = Field(alias="licence_status")
    granted_date: Optional[date] = Field(alias="licence_granted_date")
    expiry_date: Optional[date] = Field(alias="licence_expiry_date")

    @validator(
        "status",
        pre=True,
    )
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


class Operator(BaseModel):
    discs_in_possession: Optional[int]
    authdiscs: Optional[int]
    operator_id: int
    operator_name: Optional[str]
    address: Optional[str]

    @validator(
        "operator_name",
        "address",
        pre=True,
    )
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


class Service(BaseModel):
    registration_number: str
    variation_number: int
    service_number: Optional[str]
    current_traffic_area: Optional[str]
    operator: Operator
    start_point: Optional[str]
    finish_point: Optional[str]
    via: Optional[str]
    effective_date: Optional[date]
    received_date: Optional[date]
    end_date: Optional[date]
    service_type_other_details: Optional[str]
    registration_code: Optional[int]
    description: Optional[str]
    registration_status: Optional[str]
    public_text: Optional[str]
    service_type_description: Optional[str]
    short_notice: Optional[bool]
    subsidies_description: Optional[str]
    subsidies_details: Optional[str]
    last_modified: Optional[datetime]
    licence: Licence

    @validator(
        "subsidies_description",
        "subsidies_details",
        "public_text",
        "via",
        "service_type_other_details",
        "service_number",
        "current_traffic_area",
        "start_point",
        "finish_point",
        "description",
        "registration_status",
        "service_type_description",
        pre=True,
    )
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


class LocalAuthority:
    class Config:
        allow_population_by_field_name = True

    name: str = Field(alias="local_authorities")
    registration_numbers: Optional[Service]

    @validator(
        "name",
        pre=True,
    )
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


EMPTY_VALUES = ["", "n/a"]
