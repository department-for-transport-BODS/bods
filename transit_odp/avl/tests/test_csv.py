import csv
from datetime import date, datetime, timedelta
from io import StringIO

import factory
import pytest
from freezegun import freeze_time

from transit_odp.avl.constants import UPPER_THRESHOLD
from transit_odp.avl.csv.catalogue import _get_avl_data_catalogue
from transit_odp.avl.csv.validation import (
    HEADERS,
    SCHEMA_HEADERS,
    SchemaValidationResponseExporter,
    ValidationReportExporter,
    isoformat_from_time_ns,
)
from transit_odp.avl.factories import (
    AVLValidationReportFactory,
    PostPublishingCheckReportFactory,
)
from transit_odp.avl.models import PPCReportType
from transit_odp.avl.validation.factories import (
    ErrorFactory,
    IdentifierFactory,
    ResultFactory,
    SchemaErrorFactory,
    SchemaValidationResponseFactory,
    ValidationResponseFactory,
)
from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    OrganisationFactory,
)

pytestmark = pytest.mark.django_db


def test_isoformat_from_time_ns():
    """
    GIVEN a unix timestamp in nanoseconds
    WHEN I call isoformat_from_time_ns
    THEN I get an isoformat string with the timezone set to UTC
    """
    time_ns = 1630508109000000000
    expected = "2021-09-01T14:55:09+00:00"
    assert isoformat_from_time_ns(time_ns) == expected


def test_validation_exporter_no_errors():
    """
    GIVEN a ValidationResponse object with no errors
    WHEN I create a ValidationReportExporter and call to_csv_string
    THEN I am returned a valid csv formatted string with only the header row
    """
    response = ValidationResponseFactory()
    exporter = ValidationReportExporter(response)

    scsv = exporter.to_csv_string()

    f = StringIO(scsv)
    reader = csv.reader(f)
    rows = [r for r in reader]
    assert len(rows) == 1
    assert rows[0] == list(HEADERS)


def test_validation_exporter_with_errors():
    """
    GIVEN a ValidationResponse object with 1 result with 1 error
    WHEN I create a ValidationReportExporter and call to_csv_string
    THEN I am returned a valid csv formatted string with 1 header and 1 error row
    """
    identifier = IdentifierFactory(
        item_identifier="itemid1",
        line_ref="line13",
        name="OrginName",
        operator_ref="operator2",
        vehicle_journey_ref="vehicle_j_ref2",
        vehicle_ref="ref32",
    )
    error = ErrorFactory(
        level="Non-critical", details="Fake details", identifier=identifier
    )
    result = ResultFactory(errors=[error])
    response = ValidationResponseFactory(results=[result])
    exporter = ValidationReportExporter(response)

    scsv = exporter.to_csv_string()

    f = StringIO(scsv)
    reader = csv.reader(f)
    rows = [r for r in reader]
    assert len(rows) == 2
    assert rows[0] == list(HEADERS)
    *identifiers, details, refs = rows[1]

    assert details == error.details
    assert refs == ""
    expected = [
        identifier.recorded_at_time.isoformat(),
        isoformat_from_time_ns(result.header.timestamp),
        identifier.vehicle_ref,
        identifier.operator_ref,
        identifier.line_ref,
        identifier.item_identifier,
        identifier.vehicle_journey_ref,
        identifier.name,
    ]
    assert identifiers == expected


@freeze_time("2021-01-01")
def test_get_filename():
    """
    GIVEN a validation response with a particular feed id
    WHEN a ValidationReportExporter is created and get_filename is called
    THEN the filename returned should be in the format
         BODS_ValidationReport_DDMMYYYY_feedID.csv
    """
    feed_id = 345
    today = f"{datetime.now():%d%m%y}"
    response = ValidationResponseFactory(feed_id=feed_id)
    exporter = ValidationReportExporter(response)

    assert exporter.get_filename() == f"BODS_ValidationReport_{today}_{feed_id}.csv"


@freeze_time("2021-01-01")
def test_schema_exporter_get_filename():
    """
    GIVEN a validation response with a particular feed id
    WHEN a SchemaValidationReportExporter is created and get_filename is called
    THEN the filename returned should be in the format
         BODS_SchemaValidationReport_DDMMYYYY_feedID.csv
    """
    feed_id = 345
    today = f"{datetime.now():%d%m%y}"
    response = SchemaValidationResponseFactory(feed_id=feed_id)
    exporter = SchemaValidationResponseExporter(response)

    expected_filename = f"BODS_SchemaValidationReport_{today}_{feed_id}.csv"
    assert exporter.get_filename() == expected_filename


def test_schema_validation_exporter_no_errors():
    """
    GIVEN a SchemaValidationResponse object with no errors
    WHEN I create a SchemaValidationReportExporter and call to_csv_string
    THEN I am returned a valid csv formatted string with only the header row
    """
    response = SchemaValidationResponseFactory()
    exporter = SchemaValidationResponseExporter(response)

    scsv = exporter.to_csv_string()

    f = StringIO(scsv)
    reader = csv.reader(f)
    rows = [r for r in reader]
    assert len(rows) == 1
    assert rows[0] == list(SCHEMA_HEADERS)


def test_schema_validation_exporter_with_errors():
    """
    GIVEN a SchemaValidationResponse object with errors
    WHEN I create a SchemaValidationReportExporter and call to_csv_string
    THEN I am returned a valid csv formatted string with a header and error rows
    """
    errors = [SchemaErrorFactory()]
    response = SchemaValidationResponseFactory(errors=errors)
    exporter = SchemaValidationResponseExporter(response)

    scsv = exporter.to_csv_string()

    f = StringIO(scsv)
    reader = csv.reader(f)
    rows = [r for r in reader]
    assert len(rows) == 2
    assert rows[0] == list(SCHEMA_HEADERS)

    error = rows[1]
    assert error[0] == isoformat_from_time_ns(response.timestamp)
    assert error[1] == response.errors[0].message
    assert error[2] == response.errors[0].path


def test_data_catalogue_csv():
    revision = AVLDatasetRevisionFactory()
    today = datetime.now().date()
    total_reports = 8
    for n in range(0, total_reports):
        date = today - timedelta(days=n)
        AVLValidationReportFactory(
            revision=revision,
            created=date,
            non_critical_score=UPPER_THRESHOLD - 0.1,
            critical_score=UPPER_THRESHOLD + 0.1,
            vehicle_activity_count=100,
        )

    df = _get_avl_data_catalogue()
    row = df.iloc[0]
    assert row["Organisation Name"] == revision.dataset.organisation.name
    assert row["Datafeed ID"] == revision.dataset_id
    assert row["% AVL to Timetables feed matching score"] is None
    assert row["Latest matching report URL"] == ""
