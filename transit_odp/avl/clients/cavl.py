from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ValidationTaskResultStatus(str, Enum):
    DEPLOYING = "DEPLOYING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    FEED_VALID = "FEED_VALID"
    FEED_INVALID = "FEED_INVALID"


class ValidationTaskResult(BaseModel):
    url: str
    username: str
    password: Optional[str] = None
    status: ValidationTaskResultStatus = ValidationTaskResultStatus.DEPLOYING
    created: datetime
    version: Optional[str]


class FeedStatus(str, Enum):
    DEPLOYING = "DEPLOYING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    FEED_UP = "FEED_UP"
    FEED_DOWN = "FEED_DOWN"


class Feed(BaseModel):
    id: int
    publisher_id: int = Field(alias="publisherId")
    url: str
    username: str
    password: Optional[str] = None
    status: FeedStatus = FeedStatus.DEPLOYING
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
