from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from transit_odp.avl.enums import AVLFeedStatus, ValidationTaskResultStatus


class ValidationTaskResult(BaseModel):
    url: str
    username: str
    password: Optional[str] = None
    status: ValidationTaskResultStatus = ValidationTaskResultStatus.DEPLOYING.value
    created: datetime
    version: Optional[str] = None


class Feed(BaseModel):
    id: int
    publisher_id: int = Field(alias="publisherId")
    url: str
    username: str
    password: Optional[str] = None
    status: AVLFeedStatus = AVLFeedStatus.DEPLOYING.value
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    model_config = ConfigDict(populate_by_name=True)
