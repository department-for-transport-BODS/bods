import datetime
from typing import List, Optional

import attr

from transit_odp.common.utils.earlier_or_later import earlier_or_later
from transit_odp.pipelines.pipelines.dataset_etl.utils.timestamping import (
    empty_timestamp,
    starting_timestamp,
)


@attr.s(auto_attribs=True)
class ETLReport(object):

    schema_version: str = attr.ib(default="")

    creation_datetime: Optional[datetime.datetime] = attr.ib(default=None)
    modification_datetime: Optional[datetime.datetime] = attr.ib(default=None)
    import_datetime: Optional[datetime.datetime] = attr.ib(default=None)

    bounding_box: str = attr.ib(default="")

    line_count: int = attr.ib(default=0)
    first_expiring_service: Optional[datetime.datetime] = attr.ib(
        default=empty_timestamp()
    )
    last_expiring_service: Optional[datetime.datetime] = attr.ib(
        default=starting_timestamp()
    )
    first_service_start: Optional[datetime.datetime] = attr.ib(
        default=empty_timestamp()
    )
    stop_count: int = attr.ib(default=0)
    timing_point_count: int = attr.ib(default=0)

    errors: List[str] = attr.ib(factory=list)
    name: str = attr.ib(default="")

    def merge(self, right):
        # Feed publisher creation date is the earlier of the files' creation dates
        self.creation_datetime = earlier_or_later(
            self.creation_datetime, right.creation_datetime, True
        )
        # Feed publisher modification date is the later of the files' modification dates
        self.modification_datetime = earlier_or_later(
            self.modification_datetime, right.modification_datetime, False
        )

        # Similar logic for first_expiring_service, last_expiring_service and
        # first_service_start
        self.first_expiring_service = earlier_or_later(
            self.first_expiring_service, right.first_expiring_service, True
        )

        self.last_expiring_service = earlier_or_later(
            self.last_expiring_service, right.last_expiring_service, False
        )

        self.first_service_start = earlier_or_later(
            self.first_service_start, right.first_service_start, True
        )

        self.line_count += right.line_count

    def log(self, message):
        self.errors.append(message)
