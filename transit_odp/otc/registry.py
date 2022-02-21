import csv
import io
import logging
from datetime import date, datetime
from typing import List, Optional, TextIO, Tuple, Union
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, Field, ValidationError, validator

EMPTY_VALUES = ["", "n/a"]
logger = logging.getLogger(__name__)


class Registration(BaseModel):
    class Config:
        allow_population_by_field_name = True

    registration_number: str = Field(alias="Reg_No")
    variation_number: int = Field(alias="Variation Number")
    service_number: str = Field(alias="Service Number")
    current_traffic_area: str = Field(alias="Current Traffic Area")
    licence_number: str = Field(alias="Lic_No")
    discs_in_possession: Optional[int] = Field(alias="Discs in Possession")
    authdiscs: Optional[int] = Field(alias="AUTHDISCS")
    licence_granted_date: date = Field(alias="Granted_Date")
    licence_expiry_date: date = Field(alias="Exp_Date")
    description: str = Field(alias="Description")
    operator_id: int = Field(alias="Op_ID")
    operator_name: str = Field(alias="Op_Name")
    trading_name: str = Field(alias="trading_name")
    address: str = Field(alias="Address")
    start_point: str = Field(alias="start_point")
    finish_point: str = Field(alias="finish_point")
    via: str = Field(alias="via")
    effective_date: Optional[date] = Field(alias="effective_date")
    received_date: Optional[date] = Field(alias="received_date")
    end_date: Optional[date] = Field(alias="end_date")
    service_type_other_details: str = Field(alias="Service_Type_Other_Details")
    licence_status: str = Field(alias="Licence Status")
    registration_status: str = Field(alias="Registration Status")
    public_text: str = Field(alias="Pub_Text")
    service_type_description: str = Field(alias="Service_Type_Description")
    short_notice: Optional[bool] = Field(alias="Short Notice")
    subsidies_description: str = Field(alias="Subsidies_Description")
    subsidies_details: str = Field(alias="Subsidies_Details")
    auth_description: str = Field(alias="Auth_Description")
    tao_covered_by_area: str = Field(alias="TAO Covered BY Area")
    registration_code: Optional[int] = Field(alias="Registration Code")

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
            return datetime.strptime(v, "%d/%m/%y").date()
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
    status: str = Field(alias="licence_status")
    granted_date: date = Field(alias="licence_granted_date")
    expiry_date: date = Field(alias="licence_expiry_date")


class Operator(BaseModel):
    discs_in_possession: Optional[int]
    authdiscs: Optional[int]
    operator_id: int
    operator_name: str
    address: str


class Service(BaseModel):
    registration_number: str
    variation_number: int
    service_number: str
    current_traffic_area: str
    operator: Operator
    start_point: str
    finish_point: str
    via: str
    effective_date: Optional[date]
    received_date: Optional[date]
    end_date: Optional[date]
    service_type_other_details: str
    registration_code: Optional[int]
    description: str
    registration_status: str
    public_text: str
    service_type_description: str
    short_notice: Optional[bool]
    subsidies_description: str
    subsidies_details: str
    licence: Licence


def parse_csv(csvfile: TextIO, log_path="") -> List[Registration]:
    registrations = []
    reader = csv.DictReader(csvfile)
    for row in reader:
        try:
            registrations.append(Registration(**row))
        except ValidationError as e:
            msg = f"{log_path} Skipping line {reader.line_num}: {e}"
            logger.warning(msg)

    return registrations


class Registry:
    def __init__(self, registrations: List[Registration]):
        self.registrations = registrations
        self._operator_map = {}
        self._service_map = {}
        self._licence_map = {}

        for registration in self.registrations:
            licence_number = registration.licence_number
            registration_number = registration.registration_number
            service_type_description = registration.service_type_description
            operator_id = registration.operator_id

            if (registration_number, service_type_description) in self._service_map:
                continue

            if licence_number not in self._licence_map:
                licence = Licence(**registration.dict())
                self._licence_map[licence_number] = licence
            else:
                licence = self._licence_map[licence_number]

            if operator_id not in self._operator_map:
                operator = Operator(**registration.dict())
                self._operator_map[registration.operator_id] = operator
            else:
                operator = self._operator_map[registration.operator_id]

            self._service_map[
                (registration_number, service_type_description)
            ] = Service(operator=operator, licence=licence, **registration.dict())

    @classmethod
    def from_filepath(cls, paths: Union[List[str], str]):
        registrations = []
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            with open(path, "r") as csvfile:
                registrations += parse_csv(csvfile, log_path=path)

        return cls(registrations=registrations)

    @classmethod
    def from_url(cls, urls: Union[List[str], str]):
        registrations = []
        if isinstance(urls, str):
            urls = [urls]

        for url in urls:
            parsed_url = urlparse(url)
            response = requests.get(url, timeout=10)

            if not response.ok:
                logger.error(f"{url} returned a HTTP {response.status_code}")
                return cls(registrations=[])

            buffer = io.StringIO(response.text)
            registrations += parse_csv(buffer, parsed_url.path)

        return cls(registrations=registrations)

    @property
    def operators(self) -> List[Operator]:
        return list(self._operator_map.values())

    @property
    def operator_ids(self) -> List[int]:
        return list(self._operator_map.keys())

    def get_operator_by_id(self, id_: int) -> Optional[Operator]:
        return self._operator_map.get(id_)

    @property
    def services(self) -> List[Service]:
        return list(self._service_map.values())

    @property
    def service_ids(self) -> List[Tuple[str, str]]:
        return list(self._service_map.keys())

    def get_service_by_key(
        self, registration_number, service_type_description
    ) -> Optional[Service]:
        return self._service_map.get((registration_number, service_type_description))

    @property
    def licences(self) -> List[Licence]:
        return list(self._licence_map.values())

    @property
    def licence_numbers(self) -> List[str]:
        return list(self._licence_map.keys())

    def get_licence_by_number(self, licence_number: str) -> Optional[Licence]:
        return self._licence_map.get(licence_number)
