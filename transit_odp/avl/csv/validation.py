import csv
import io
from datetime import datetime, timezone
from typing import Iterator, List

from transit_odp.avl.validation.models import (
    Identifier,
    SchemaError,
    SchemaValidationResponse,
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

SCHEMA_HEADERS = ("Packet Timestamp", "Message", "Element")

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
        results = list(self.response.results)
        for result in results:
            for error in result.errors:
                identifier: Identifier = error.identifier

                if identifier.recorded_at_time is not None:
                    recorded_at_time = identifier.recorded_at_time.isoformat()
                else:
                    recorded_at_time = ""

                yield [
                    recorded_at_time,
                    isoformat_from_time_ns(result.header.timestamp),
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


class SchemaValidationResponseExporter:
    def __init__(self, response: SchemaValidationResponse):
        self.response = response

    def to_csv_string(self):
        csvfile = io.StringIO()
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(SCHEMA_HEADERS)
        for error in self.response.errors:
            writer.writerow(self.get_row(error))
        output = csvfile.getvalue()
        csvfile.close()
        return output

    def get_row(self, error: SchemaError):
        return [
            isoformat_from_time_ns(self.response.timestamp),
            error.message,
            error.path,
        ]

    def get_filename(self):
        now = datetime.now().date()
        filename = (
            f"BODS_SchemaValidationReport_{now:%d%m%y}_{self.response.feed_id}.csv"
        )
        return filename
