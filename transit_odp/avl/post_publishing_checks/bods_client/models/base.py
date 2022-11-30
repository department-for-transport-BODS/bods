from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from pydantic.fields import Field

from ..types import NOCs


class BaseDataset(BaseModel):
    id: int
    url: str
    operator_name: str = Field(alias="operatorName")
    name: str
    description: str
    comment: str
    status: str
    nocs: List[str] = Field(alias="noc")
    created: datetime
    modified: datetime


class BaseAPIParams(BaseModel):
    class Config:
        allow_population_by_field_name = True

    nocs: Optional[NOCs] = Field(None, alias="noc")
    status: Optional[str] = None
    limit: int = 25
    offset: int = 0


class BaseAPIResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]


class APIError(BaseModel):
    status_code: int
    reason: str


class AdminAreas(BaseModel):
    atco_code: str
    name: str


class Locality(BaseModel):
    gazetteer_id: str
    name: str


class BoundingBox(BaseModel):
    min_longitude: float
    min_latitude: float
    max_longitude: float
    max_latitude: float

    def list(self) -> List[float]:
        return [
            self.min_longitude,
            self.min_latitude,
            self.max_longitude,
            self.max_latitude,
        ]

    def csv(self) -> str:
        return ",".join(str(f) for f in self.list())


class BoundingBoxMixin(BaseModel):
    bounding_box: Optional[BoundingBox] = Field(None, alias="boundingBox")

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)

        if "boundingBox" in d and self.bounding_box is not None:
            d["boundingBox"] = self.bounding_box.csv()

        return d
