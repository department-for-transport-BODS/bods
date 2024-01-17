from pathlib import Path

import pytest
from lxml import etree

_HERE = Path(__file__)
_DATA = _HERE.parent / "data"


@pytest.fixture()
def flexible_stops():
    flexible_stop_path = _DATA / "flexible_stop.xml"
    with flexible_stop_path.open("r") as f:
        stop = etree.parse(f)
        yield stop.getroot()
