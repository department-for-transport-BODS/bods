import csv
import zipfile
from io import TextIOWrapper

import pytest

from transit_odp.data_quality.pti.factories import ViolationFactory
from transit_odp.data_quality.pti.report import PTI_CSV_COLUMNS, UTF8, PTIReport

pytestmark = pytest.mark.django_db


def test_to_zip_as_bytes():
    """
    Given I have a violation and call write_violation
    Then result.to_zip_as_bytes returns a zip file
    """
    violation = ViolationFactory()
    filename = "pti_results_223.csv"

    result = PTIReport(filename)
    result.write_violation(violation)

    with zipfile.ZipFile(result.to_zip_as_bytes(), "r") as zf:
        assert filename in zf.namelist()

        with zf.open(filename, "r") as fp:
            reader = csv.reader(TextIOWrapper(fp, UTF8))
            columns, first = reader
            assert PTI_CSV_COLUMNS == tuple(columns)
            assert [str(item) for item in violation.to_bods_csv()] == first
