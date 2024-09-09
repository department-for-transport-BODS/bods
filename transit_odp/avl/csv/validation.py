import csv
import io
from datetime import datetime, timezone
from typing import Iterator, List

from transit_odp.avl.validation.models import (
    Identifier,
    ValidationResponse,
)

HEADERS = (
    "RecordedAtTime",
    "Time (of SIRI packet)",
    "VehicleRef",
    "OperatorRef",
    "LineRef",
    "ItemIdentifier",
    "VehicleJourneyRef",
    "Name",
    "Details",
    "Reference",
)

NANO = 1_000_000_000


def isoformat_from_time_ns(timestamp: int, tzinfo=timezone.utc):
    timestamp = datetime.utcfromtimestamp(timestamp // NANO)
    timestamp_str = timestamp.replace(tzinfo=tzinfo).isoformat()
    return timestamp_str


class ValidationReportExporter:
    def __init__(self, response: ValidationResponse):
        self.response = response

    def to_csv_string(self):
        csvfile = io.StringIO()
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(HEADERS)
        writer.writerows(self.get_rows())
        output = csvfile.getvalue()
        csvfile.close()
        return output

    def get_rows(self) -> Iterator[List[str]]:
        results = list(self.response.errors)
        for result in results:
            for error in result.errors:
                identifier: Identifier = error.identifier

                if identifier.recorded_at_time is not None:
                    recorded_at_time = identifier.recorded_at_time
                else:
                    recorded_at_time = ""

                yield [
                    recorded_at_time,
                    result.header.timestamp,
                    identifier.vehicle_ref,
                    identifier.operator_ref,
                    identifier.line_ref,
                    identifier.item_identifier,
                    identifier.vehicle_journey_ref,
                    identifier.name,
                    error.details,
                    "",
                ]

    def get_filename(self):
        now = datetime.now().date()
        filename = f"BODS_ValidationReport_{now:%d%m%y}_{self.response.feed_id}.csv"
        return filename
