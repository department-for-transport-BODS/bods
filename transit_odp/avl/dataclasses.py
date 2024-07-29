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
    id: str
    publisher_id: str = Field(alias="publisherId")
    status: AVLFeedStatus = AVLFeedStatus.DEPLOYING.value # todo - figure out if this needs remapping
    last_avl_data_received_date_time: Optional[str] = Field(alias="lastAvlDataReceivedDateTime")
    heartbeat_last_received_date_time: Optional[str] = Field(alias="heartbeatLastReceivedDateTime")
    service_start_datetime: Optional[str] = Field(alias="serviceStartDatetime")
    service_end_datetime: Optional[str] = Field(alias="serviceEndDatetime")
    api_key: str = Field(alias="apiKey")
