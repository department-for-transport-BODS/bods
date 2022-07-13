import csv
import zipfile
from io import StringIO, TextIOWrapper

import factory
import pytest

from transit_odp.data_quality.pti.constants import (
    REF_PREFIX,
    REF_SUFFIX,
    REF_URL,
    get_important_note,
)
from transit_odp.data_quality.pti.factories import ViolationFactory
from transit_odp.data_quality.pti.report import (
    PTI_CSV_COLUMNS,
    PTI_SUMMARY_COLUMNS,
    UTF8,
    PTIReport,
)

pytestmark = pytest.mark.django_db


def test_to_zip_as_bytes():
    """
    Given I have a violation and call write_violation
    Then result.to_zip_as_bytes returns a zip file
    """
    violation = ViolationFactory()
    filename = "pti_results_223.csv"
    full_filename = f"BODS_TXC_validation_{filename}"

    result = PTIReport(filename, [violation])

    with zipfile.ZipFile(result.to_zip_as_bytes(), "r") as zf:
        for file_ in zf.namelist():
            assert file_.endswith(filename)

        with zf.open(full_filename, "r") as fp:
            reader = csv.reader(TextIOWrapper(fp, UTF8))
            columns, first = reader
            assert tuple(PTI_CSV_COLUMNS.values()) == tuple(columns)
            assert first[0] == violation.filename
            assert first[1] == str(violation.line)
            assert first[2] == violation.name
            assert first[3] == violation.observation.category
            assert first[4] == violation.observation.details
            assert first[5] == REF_PREFIX + "2.4.3" + REF_SUFFIX + REF_URL
            assert first[6] == get_important_note()


def test_pti_summary_report():
    bank_hol_total = 5
    journey_pattern_total = 6
    service_total = 7

    violations = []
    violations += ViolationFactory.create_batch(
        bank_hol_total,
        filename=factory.Sequence(lambda n: f"File{n}"),
        line=factory.Sequence(lambda n: n),
        name="BankHolidayOperation",
        observation__number=43,
        observation__details="Mandatory elements incorrect in 'BankHolidayOperation'",
    )
    violations += ViolationFactory.create_batch(
        journey_pattern_total,
        filename=factory.Sequence(lambda n: f"File{n}"),
        line=factory.Sequence(lambda n: n),
        name="JourneyPatternTimingLink",
        observation__number=38,
        observation__details=(
            "Mandatory elements incorrect in 'JourneyPatternTimingLink'"
        ),
    )
    violations += ViolationFactory.create_batch(
        service_total,
        filename=factory.Sequence(lambda n: f"File{n}"),
        line=factory.Sequence(lambda n: n),
        name="Service",
        observation__number=105,
        observation__details="Mandatory element 'PublicUse' missing",
    )

    file_ending = ".csv"
    report = PTIReport(file_ending, violations)
    summary_csv = StringIO(report.get_pti_summary_report())
    reader = csv.reader(summary_csv)
    headers, *rows = list(reader)
    assert headers == list(PTI_SUMMARY_COLUMNS.values())
    assert len(rows) == 3
    first, second, third = sorted(rows, key=lambda n: n[1])

    assert first[1] == str(bank_hol_total)
    assert first[2] == "BankHolidayOperation"

    assert second[1] == str(journey_pattern_total)
    assert second[2] == "JourneyPatternTimingLink"

    assert third[1] == str(service_total)
    assert third[2] == "Service"


def test_pti_report():
    bank_hol_total = 5
    journey_pattern_total = 6
    service_total = 7

    violations = []
    violations += ViolationFactory.create_batch(
        bank_hol_total,
        filename=factory.Sequence(lambda n: f"File{n}"),
        line=factory.Sequence(lambda n: n),
        name="BankHolidayOperation",
        observation__number=43,
        observation__details="Mandatory elements incorrect in 'BankHolidayOperation'",
    )
    violations += ViolationFactory.create_batch(
        journey_pattern_total,
        filename=factory.Sequence(lambda n: f"File{n}"),
        line=factory.Sequence(lambda n: n),
        name="JourneyPatternTimingLink",
        observation__number=38,
        observation__details=(
            "Mandatory elements incorrect in 'JourneyPatternTimingLink'"
        ),
    )
    violations += ViolationFactory.create_batch(
        service_total,
        filename=factory.Sequence(lambda n: f"File{n}"),
        line=factory.Sequence(lambda n: n),
        name="Service",
        observation__number=105,
        observation__details="Mandatory element 'PublicUse' missing",
    )

    file_ending = ".csv"
    report = PTIReport(file_ending, violations)
    summary_csv = StringIO(report.get_pti_report())
    reader = csv.reader(summary_csv)
    _, *rows = list(reader)
    assert len(rows) == bank_hol_total + journey_pattern_total + service_total
