from datetime import datetime
from typing import Optional

from pydantic.fields import Field
from pydantic.main import BaseModel

from ..types import NOCs
from .base import BoundingBoxMixin


class BaseAVLParams(BaseModel):
    class Config:
        allow_population_by_field_name = True


class SIRIVMParams(BaseAVLParams, BoundingBoxMixin):
    class Config(BaseAVLParams.Config):
        pass

    operator_refs: Optional[NOCs] = Field(None, alias="operatorRef")
    line_ref: Optional[str] = Field(None, alias="lineRef")
    producer_ref: Optional[str] = Field(None, alias="producerRef")
    origin_ref: Optional[str] = Field(None, alias="originRef")
    destinaton_ref: Optional[str] = Field(None, alias="destinationRef")
    vehicle_ref: Optional[str] = Field(None, alias="vehicleRef")


class GTFSRTParams(BaseAVLParams, BoundingBoxMixin):
    class Config(BaseAVLParams.Config):
        pass

    route_id: Optional[str] = Field(None, alias="routeId")
    start_time_after: Optional[datetime] = Field(None, alias="startTimeAfter")
    start_time_before: Optional[datetime] = Field(None, alias="startTimeBefore")
