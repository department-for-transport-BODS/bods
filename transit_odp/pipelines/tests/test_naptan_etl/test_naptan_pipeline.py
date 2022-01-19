from pathlib import Path
from unittest.mock import patch

import pytest

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    LocalityFactory,
    StopPointFactory,
)
from transit_odp.naptan.models import StopPoint
from transit_odp.pipelines.pipelines.naptan_etl.main import run

pytestmark = pytest.mark.django_db
mut = "transit_odp.pipelines.pipelines.naptan_etl.main"
HERE = Path(__file__)
TEST_DATA_DIR = HERE.parent / "data"
NPTG = TEST_DATA_DIR / "Nptg_localities_in_one_admin_area.xml"
NAPTAN = TEST_DATA_DIR / "naptan_data_variations"


@patch(f"{mut}.get_latest_naptan_xml")
@patch(f"{mut}.get_latest_nptg")
def test_naptan_pipeline_runs(get_latest_nptg, get_latest_naptan_xml):
    get_latest_nptg.return_value = str(NPTG)
    get_latest_naptan_xml.return_value = str(NAPTAN / "match_nptg.xml")

    run()
    assert StopPoint.objects.count() == 4


@patch(f"{mut}.get_latest_naptan_xml")
@patch(f"{mut}.get_latest_nptg")
def test_naptan_missing_admin_area(get_latest_nptg, get_latest_naptan_xml):
    get_latest_nptg.return_value = str(NPTG)
    get_latest_naptan_xml.return_value = str(NAPTAN / "missing_admin_area.xml")

    run()
    assert StopPoint.objects.count() == 3


@patch(f"{mut}.get_latest_naptan_xml")
@patch(f"{mut}.get_latest_nptg")
def test_naptan_missing_locality(get_latest_nptg, get_latest_naptan_xml):
    get_latest_nptg.return_value = str(NPTG)
    get_latest_naptan_xml.return_value = str(NAPTAN / "missing_locality.xml")

    run()
    assert StopPoint.objects.count() == 3


@patch(f"{mut}.get_latest_naptan_xml")
@patch(f"{mut}.get_latest_nptg")
def test_naptan_pipeline_updates_data(get_latest_nptg, get_latest_naptan_xml):
    aa = AdminAreaFactory(name="Oldton")
    locality = LocalityFactory(name="OldVille", admin_area=aa)
    for index in range(1, 5):
        # These stop points are in the xml and datebase so we test update code
        StopPointFactory(atco_code=f"01000000{index}", admin_area=aa, locality=locality)

    get_latest_nptg.return_value = str(NPTG)
    get_latest_naptan_xml.return_value = str(NAPTAN / "match_nptg.xml")
    run()

    for stop in StopPoint.objects.all():
        assert stop.admin_area.name == "National - National Rail"
        assert stop.locality.name == "Ashgrove"
