from datetime import date, datetime
from typing import Optional, OrderedDict

from django.utils.timezone import make_aware
from pydantic import ConfigDict, Field, field_validator, validator
from pydantic.main import BaseModel


class Registration(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    registration_number: str = Field(alias="registrationNumber", max_length=20)
    variation_number: int = Field(alias="variationNumber")
    other_service_number: Optional[str] = Field(None, alias="otherServiceNumber")
    service_number: Optional[str] = Field(None, alias="serviceNumber", max_length=1000)
    current_traffic_area: Optional[str] = Field(
        None, alias="trafficAreaId", max_length=1
    )
    licence_number: Optional[str] = Field(None, alias="licenceNumber")
    discs_in_possession: Optional[int] = Field(None, alias="discsInPossession")
    authdiscs: Optional[int] = Field(None, alias="authDiscs")
    licence_granted_date: Optional[date] = Field(None, alias="grantedDate")
    licence_expiry_date: Optional[date] = Field(None, alias="expiryDate")
    description: Optional[str] = Field(None, alias="licenceType", max_length=25)
    operator_id: int = Field(alias="operatorId")
    operator_name: Optional[str] = Field(None, alias="operatorName")
    trading_name: Optional[str] = Field(None, alias="tradingName")
    address: str = Field(alias="contactAddress1")
    start_point: Optional[str] = Field(None, alias="startPoint")
    finish_point: Optional[str] = Field(None, alias="finishPoint")
    via: Optional[str] = Field(None, alias="via")
    effective_date: Optional[date] = Field(None, alias="effectiveDate")
    received_date: Optional[date] = Field(None, alias="receivedDate")
    end_date: Optional[date] = Field(None, alias="endDate")
    service_type_other_details: Optional[str] = Field(None, alias="otherDetails")
    licence_status: Optional[str] = Field(None, alias="licenceStatus")
    registration_status: Optional[str] = Field(
        None, alias="registrationStatus", max_length=20
    )
    public_text: Optional[str] = Field(None, alias="publicationText")
    service_type_description: Optional[str] = Field(
        None, alias="busServiceTypeDescription", max_length=1000
    )
    short_notice: Optional[bool] = Field(None, alias="isShortNotice")
    subsidies_description: Optional[str] = Field(None, alias="subsidised", max_length=7)
    subsidies_details: Optional[str] = Field(None, alias="subsidyDetail")
    auth_description: Optional[str] = Field(None, alias="localAuthorities")
    tao_covered_by_area: Optional[str] = Field(None, alias="taoCoveredByArea")
    registration_code: Optional[int] = Field(None, alias="registrationCode")
    last_modified: Optional[datetime] = Field(None, alias="lastModifiedOn")
    local_authorities: Optional[str] = Field(None, alias="localAuthorities")

    @field_validator(
        "licence_granted_date",
        "licence_expiry_date",
        "effective_date",
        "received_date",
        "end_date",
        mode="before",
    )
    @classmethod
    def parse_date(cls, v):
        if v:
            return datetime.strptime(v, "%d/%m/%Y").date()
        return

    @field_validator("last_modified", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if v:
            last_modified = datetime.strptime(v, "%d/%m/%Y %H:%M:%S")
            last_modified = make_aware(last_modified)
            return last_modified
        return

    @field_validator(
        "variation_number",
        "discs_in_possession",
        "authdiscs",
        "operator_id",
        "end_date",
        "short_notice",
        "registration_code",
        mode="before",
    )
    @classmethod
    def empty_to_none(cls, v):
        if v == "":
            return
        return v

    @field_validator(
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
        mode="before",
    )
    @classmethod
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v

    @field_validator("registration_number", "licence_number")
    @classmethod
    def validate_not_empty(cls, v):
        # Note all strings are empty by default, these are the only ones that
        # cannot be optional
        if v.lower() in EMPTY_VALUES:
            raise ValueError(f"{v} is an empty value but it is required")
        return v

    @field_validator("registration_status")
    @classmethod
    def validate_registration_status(cls, v):
        if v is not None and v not in ALLOWED_REGISTRATION_STATUSES:
            raise ValueError(f"Invalid registration status: {v}")
        return v

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.

    @validator("service_number", pre=True)
    def combine_service_numbers(cls, v, values):
        other_service_number = values.get("other_service_number", "")
        if not other_service_number:
            return v

        # Function to split a string at different delimiters and return a list of numbers
        def split_at_delimiters(s):
            delimiters = [",", " ", "-", "|"]
            numbers = []
            current_number = ""
            for char in s:
                if char in delimiters:
                    if current_number.strip():
                        numbers.append(current_number.strip())
                    current_number = ""
                else:
                    current_number += char
            if current_number.strip():
                numbers.append(current_number.strip())
            return numbers

        service_numbers = split_at_delimiters(v) if v else []
        other_service_numbers = (
            split_at_delimiters(other_service_number) if other_service_number else []
        )

        combined_service_numbers = list(
            OrderedDict.fromkeys(service_numbers + other_service_numbers)
        )
        result = "|".join(combined_service_numbers)
        return result


class Licence(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    number: str = Field(alias="licence_number")
    status: Optional[str] = Field(None, alias="licence_status")
    granted_date: Optional[date] = Field(None, alias="licence_granted_date")
    expiry_date: Optional[date] = Field(None, alias="licence_expiry_date")

    @field_validator("status", mode="before")
    @classmethod
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


class Operator(BaseModel):
    discs_in_possession: Optional[int] = None
    authdiscs: Optional[int] = None
    operator_id: int
    operator_name: Optional[str] = None
    address: Optional[str] = None

    @field_validator("operator_name", "address", mode="before")
    @classmethod
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


class Service(BaseModel):
    registration_number: str
    variation_number: int
    service_number: Optional[str] = None
    current_traffic_area: Optional[str] = None
    operator: Operator
    start_point: Optional[str] = None
    finish_point: Optional[str] = None
    via: Optional[str] = None
    effective_date: Optional[date] = None
    received_date: Optional[date] = None
    end_date: Optional[date] = None
    service_type_other_details: Optional[str] = None
    registration_code: Optional[int] = None
    description: Optional[str] = None
    registration_status: Optional[str] = None
    public_text: Optional[str] = None
    service_type_description: Optional[str] = None
    short_notice: Optional[bool] = None
    subsidies_description: Optional[str] = None
    subsidies_details: Optional[str] = None
    last_modified: Optional[datetime] = None
    licence: Licence

    @field_validator(
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
        mode="before",
    )
    @classmethod
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


class LocalAuthority(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    registration_number: str = Field(alias="registrationNumber")
    local_authorities: Optional[str] = Field(None, alias="localAuthorities")

    @field_validator("local_authorities", mode="before")
    @classmethod
    def none_to_str(cls, v):
        if v is None:
            return ""
        return v


EMPTY_VALUES = ["", "n/a"]
ALLOWED_REGISTRATION_STATUSES = [
    "Admin Cancelled",
    "Cancelled",
    "New",
    "Refused",
    "Surrendered",
    "Revoked",
    "CNS",
    "Cancellation",
    "Expired",
    "Withdrawn",
    "Variation",
    "Registered",
]
