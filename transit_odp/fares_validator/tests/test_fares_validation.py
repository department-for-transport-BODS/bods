from pathlib import Path

import pytest
from django.core.files import File

from transit_odp.fares_validator.views.fares_validation import get_fares_validator

DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.parametrize(
    (
        "test_pass",
        "expected",
    ),
    [
        (True, 0),
        (False, 1),
    ],
)
def test_fares_validation_xml(test_pass, expected):
    """
    Given a revision with a file containing pti violations
    When we call `get_violations` on the pti validator
    Then the number of violations returned is greater than 0
    """
    if test_pass:
        filepath = DATA_DIR / "fares_test_xml_pass.xml"
    else:
        filepath = DATA_DIR / "fares_test_xml_fail.xml"
    fares_validator = get_fares_validator()
    with open(filepath, "rb") as zout:
        violations = fares_validator.get_violations(
            File(zout, name="fares_test_xml_1.xml"), 1
        )
    assert len(violations) == expected


@pytest.mark.parametrize(
    (
        "test_pass",
        "expected",
    ),
    [
        (True, 0),
        (False, 5),
    ],
)
def test_fares_validation_zip(test_pass, expected):
    """
    Given a revision with a zipfile containing no pti violations
    When we call `get_violations` on the pti validator
    Then the number of violations returned is 0
    """
    if test_pass:
        filepath = DATA_DIR / "fares_test_zip_pass.zip"
    else:
        filepath = DATA_DIR / "fares_test_zip_fail.zip"
    fares_validator = get_fares_validator()
    with open(filepath, "rb") as zout:
        violations = fares_validator.get_violations(File(zout, name="test_zip.zip"), 2)
    assert len(violations) == expected
