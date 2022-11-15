from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from pydantic.fields import Field

from ..types import AdminAreasType
from .base import AdminAreas, BaseAPIParams, BaseAPIResponse, BaseDataset, Locality


class Timetable(BaseDataset):
    lines: List[str]
    localities: List[Locality]
    admin_areas: List[AdminAreas] = Field(alias="adminAreas")
    first_start_date: datetime = Field(alias="firstStartDate")
    first_end_date: datetime = Field(None, alias="firstEndDate")
    last_end_date: datetime = Field(None, alias="lastEndDate")
    dq_score: str = Field(alias="dqScore")
    dq_rag: str = Field(alias="dqRag")
    bods_compliance: bool = Field(None, alias="bodsCompliance")


class TimetableParams(BaseAPIParams):
    class Config(BaseAPIParams.Config):
        pass

    admin_areas: Optional[AdminAreasType] = Field(None, alias="adminArea")
    search: Optional[str] = None
    modified_date: Optional[datetime] = Field(None, alias="modifiedDate")
    start_date_start: Optional[datetime] = Field(None, alias="startDateEnd")
    start_date_end: Optional[datetime] = Field(None, alias="startDateStart")
    end_date_start: Optional[datetime] = Field(None, alias="endDateStart")
    end_date_end: Optional[datetime] = Field(None, alias="endDateEnd")
    dq_rag: Optional[str] = Field(None, alias="dqRag")
    bods_compliance: Optional[bool] = Field(None, alias="bodsCompliance")


class TimetableResponse(BaseAPIResponse):
    results: List[Timetable]


class TxcFile(BaseModel):
    id: int
    dataset_id: int
    schema_version: str
    revision_number: int
    modification: str
    creation_datetime: datetime
    modification_datetime: datetime
    filename: str
    service_code: str
    national_operator_code: str
    licence_number: str
    operating_period_start_date: Optional[str] = None
    operating_period_end_date: Optional[str] = None
    public_use: bool
    line_names: List[str]
    origin: str
    destination: str


class TxcFileParams(BaseModel):
    class Config:
        allow_population_by_field_name = True

    noc: Optional[str] = None
    line_name: Optional[str] = None
    limit: int = 25
    offset: int = 0


class TxcFileResponse(BaseAPIResponse):
    results: List[TxcFile]
