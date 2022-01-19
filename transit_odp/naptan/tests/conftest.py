from pathlib import Path

import pytest
from lxml import etree

_HERE = Path(__file__)
_DATA = _HERE.parent / "data"


@pytest.fixture()
def ukos_stop():
    ukos_stop_path = _DATA / "ukos_stop.xml"
    with ukos_stop_path.open("r") as f:
        stop = etree.parse(f)
        yield stop.getroot()


@pytest.fixture()
def wgs_stop():
    ukos_stop_path = _DATA / "wgs_stop.xml"
    with ukos_stop_path.open("r") as f:
        stop = etree.parse(f)
        yield stop.getroot()
