from pathlib import Path

import pytest
from django.core.files import File

from transit_odp.fares_validator.types import Violation
from transit_odp.fares_validator.views.validators import FaresValidator

DATA_DIR = Path(__file__).parent / "data"
FARES_SCHEMA = Path(__file__).parent.parent / "schema" / "fares_schema.json"


@pytest.mark.parametrize(
    (
        "test_pass",
        "expected",
    ),
    [
        (True, True),
        (False, False),
    ],
)
def test_fares_validators_is_valid(test_pass, expected):
    if test_pass:
        filepath = DATA_DIR / "fares_test_xml_pass.xml"
    else:
        filepath = DATA_DIR / "fares_test_xml_fail.xml"

    with FARES_SCHEMA.open("r") as f:
        fares_validator = FaresValidator(f)
        with open(filepath, "rb") as zout:
            result = fares_validator.is_valid(File(zout, name="fares_test_xml.xml"))
    assert result == expected


@pytest.mark.parametrize(
    (
        "test_pass",
        "expected",
    ),
    [
        (True, []),
        (
            False,
            [
                Violation(
                    line=1819,
                    filename="fares_test_xml.xml",
                    observation="Element 'TripType' is missing within 'RoundTrip'",
                    category="Conditions",
                ),
            ],
        ),
    ],
)
def test_fares_validators_violations(test_pass, expected):
    if test_pass:
        filepath = DATA_DIR / "fares_test_xml_pass.xml"
    else:
        filepath = DATA_DIR / "fares_test_xml_fail.xml"

    with FARES_SCHEMA.open("r") as f:
        fares_validator = FaresValidator(f)
        with open(filepath, "rb") as zout:
            fares_validator.is_valid(File(zout, name="fares_test_xml.xml"))
            result = fares_validator.violations
    assert result == expected
