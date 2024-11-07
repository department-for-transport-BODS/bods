from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from transit_odp.avl.constants import AVL_API_STATUS_MAP
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
    status: str
    last_avl_data_received_date_time: Optional[str] = Field(
        alias="lastAvlDataReceivedDateTime"
    )
    heartbeat_last_received_date_time: Optional[str] = Field(
        alias="heartbeatLastReceivedDateTime"
    )
    service_start_datetime: Optional[str] = Field(alias="serviceStartDatetime")
    service_end_datetime: Optional[str] = Field(alias="serviceEndDatetime")
    api_key: str = Field(alias="apiKey")
    model_config = ConfigDict(populate_by_name=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        mapped_status = AVL_API_STATUS_MAP.get(self.status)

        if mapped_status is not None:
            self.status = mapped_status

class ConsumerSubscriptionQueryParams(BaseModel):
    subscription_id: str
    bounding_box: Optional[str] = None
    operator_ref: Optional[str] = None
    vehicle_ref: Optional[str] = None
    line_ref: Optional[str] = None
    producer_ref: Optional[str] = None
    origin_ref: Optional[str] = None
    destination_ref: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

class ConsumerSubscription(BaseModel):
    id: str
    name: str
    subscription_id: str
    status: str
    url: str
    requestor_ref: int
    update_interval: int
    heartbeat_interval: int
    request_timestamp: str
    initial_termination_time: str
    query_params: ConsumerSubscriptionQueryParams
    model_config = ConfigDict(populate_by_name=True)
