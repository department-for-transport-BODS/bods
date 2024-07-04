from pathlib import Path

import pytest

from transit_odp.data_quality.pti.factories import SchemaFactory
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.timetables.pti import PTI_PATH

DATA_DIR = Path(__file__).parent / "data"
pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("bodp3615stoppoints.xml", True),
        ("bodp3615stoppointsfail2month.xml", False),
        ("bodp3615stoppointsfailnodate.xml", False),
        ("stoppointsinheritfromservice2months.xml", True),
        ("stoppointsinheritfromservice2monthsplus.xml", False),
        ("stoppointsinheritstartdatefromservice.xml", True),
        ("stoppointsinheritenddatefromservice.xml", True),
    ],
)
def test_non_naptan_stop_points(filename, expected):

    OBSERVATION_ID = 28
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc_path = DATA_DIR / filename
    with txc_path.open("r") as txc:
        is_valid = pti.is_valid(txc)
    assert is_valid == expected
