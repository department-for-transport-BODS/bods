import csv
import zipfile
from io import TextIOWrapper

import pytest

from transit_odp.data_quality.models.report import PTIValidationResult
from transit_odp.data_quality.pti.factories import ViolationFactory
from transit_odp.data_quality.pti.report import PTI_CSV_COLUMNS, UTF8
from transit_odp.organisation.factories import DatasetRevisionFactory

pytestmark = pytest.mark.django_db


def test_from_pti_violations(pti_unenforced):
    revision = DatasetRevisionFactory()
    violations = [ViolationFactory()]

    PTIValidationResult.from_pti_violations(
        revision=revision, violations=violations
    ).save()

    validation_result = PTIValidationResult.objects.get(revision_id=revision.id)
    expected_filename = "pti_observations.csv"
    expected_zipname = f"pti_validation_revision_{revision.id}.zip"
    assert validation_result.report.name == expected_zipname
    with zipfile.ZipFile(validation_result.report, "r") as zf:
        assert expected_filename in zf.namelist()
        with zf.open(expected_filename, "r") as fp:
            reader = csv.reader(TextIOWrapper(fp, UTF8))
            columns, first = reader
            assert PTI_CSV_COLUMNS == tuple(columns)
            for violation in violations:
                assert [str(item) for item in violation.to_bods_csv()] == first


def test_important_information_black_after_pti_deadline(pti_enforced):
    revision = DatasetRevisionFactory()
    violations = [ViolationFactory()]

    PTIValidationResult.from_pti_violations(
        revision=revision, violations=violations
    ).save()

    validation_result = PTIValidationResult.objects.get(revision_id=revision.id)
    expected_filename = "pti_observations.csv"
    with zipfile.ZipFile(validation_result.report, "r") as zf:
        with zf.open(expected_filename, "r") as fp:
            reader = csv.reader(TextIOWrapper(fp, UTF8))
            columns, first = reader
            assert PTI_CSV_COLUMNS == tuple(columns)
            for violation in violations:
                assert violation.to_bods_csv()[-1] == ""
