from pathlib import Path

import pytest

from transit_odp.data_quality.pti.factories import SchemaFactory
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile, XMLFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.timetables.utils import PTI_PATH

DATA_DIR = Path(__file__).parent / "data"

TXC = """<?xml version="1.0" encoding="UTF-8"?>
    <TransXChange xmlns="http://www.transxchange.org.uk/" xml:lang="en"
    SchemaVersion="2.4" {0}></TransXChange>
    """


@pytest.mark.parametrize(
    ("version", "modification_date", "creation_date", "expected"),
    [
        ("0", "2004-06-09T14:20:00-05:00", "2004-06-09T14:20:00-05:00", True),
        ("0", "2004-06-02T13:20:00-05:00", "2004-06-01T13:20:00-05:00", False),
        ("1", "2004-06-09T14:20:00-05:00", "2004-06-09T14:20:00-05:00", False),
        ("1", "2004-06-01T14:20:00-05:00", "2004-06-09T14:20:00-05:00", False),
        ("1", "2004-06-10T14:20:00-05:00", "2004-06-09T14:20:00-05:00", True),
    ],
)
def test_validate_modification_date_with_revision(
    version, modification_date, creation_date, expected
):
    modification_date = 'ModificationDateTime="{0}"'.format(modification_date)
    creation_date = 'CreationDateTime="{0}"'.format(creation_date)
    attributes = 'RevisionNumber="{0}" {1} {2}'
    attributes = attributes.format(version, modification_date, creation_date)
    xml = TXC.format(attributes)

    OBSERVATION_ID = 2
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = XMLFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("version", "modification", "expected"),
    [
        ("0", "new", True),
        ("1", "revise", True),
        ("10", "new", False),
        ("0", "revise", False),
        ("0", "delete", False),
        ("1", "delete", False),
    ],
)
def test_validate_modification(version, modification, expected):
    attributes = 'RevisionNumber="{0}" Modification="{1}"'
    attributes = attributes.format(version, modification)
    xml = TXC.format(attributes)

    OBSERVATION_ID = 3
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = XMLFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected
