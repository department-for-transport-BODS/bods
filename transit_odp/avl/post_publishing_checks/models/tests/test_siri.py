from datetime import datetime, timezone
from pathlib import Path

import pytest

from transit_odp.avl.post_publishing_checks.models import Siri

pytestmark = pytest.mark.django_db

DATA_DIR = Path(__file__).parent / "data"


def test_parse_siri():
    siri_filename = str(DATA_DIR / "siri_sample.xml")
    with open(siri_filename, "rt") as fp:
        content = fp.read()
        parsed_siri = Siri.from_string(content)
        sd = parsed_siri.service_delivery
        assert sd.response_timestamp == datetime(
            2023, 1, 25, 17, 2, 0, 971080, timezone.utc
        )
        vmd = sd.vehicle_monitoring_delivery
        assert vmd.response_timestamp == datetime(
            2023, 1, 25, 17, 2, 1, 71080, timezone.utc
        )
        activities = vmd.vehicle_activities
        assert len(activities) == 2

        assert activities[0].recorded_at_time == datetime(
            2023, 1, 25, 17, 1, 47, 0, timezone.utc
        )
        mvj = activities[0].monitored_vehicle_journey
        assert mvj.line_ref == "22"
        assert mvj.direction_ref == "OUTBOUND"
        assert mvj.direction_ref_linenum == 16
        assert mvj.framed_vehicle_journey_ref.dated_vehicle_journey_ref == "65"
        assert mvj.published_line_name == "22"
        assert mvj.operator_ref == "STWS"
        assert mvj.origin_ref == "6170247"
        assert mvj.origin_ref_linenum == 23
        assert mvj.destination_ref == "6170702"
        assert mvj.destination_ref_linenum == 25
        assert mvj.destination_name == "Strathmore Park"
        assert mvj.block_ref == "6502"
        assert mvj.block_ref_linenum == 33

        assert activities[1].recorded_at_time == datetime(
            2023, 1, 25, 17, 1, 48, 0, timezone.utc
        )
        mvj = activities[1].monitored_vehicle_journey
        assert mvj.line_ref == "59"
        assert mvj.direction_ref == "INBOUND"
        assert mvj.direction_ref_linenum == 48
        assert mvj.framed_vehicle_journey_ref.dated_vehicle_journey_ref == "1096"
        assert mvj.published_line_name == "59"
        assert mvj.operator_ref == "SBLB"
        assert mvj.origin_ref == "639003812"
        assert mvj.origin_ref_linenum == 55
        assert mvj.destination_ref == "639001311"
        assert mvj.destination_ref_linenum == 57
        assert mvj.destination_name == "Howes Road"
        assert mvj.block_ref is None
        assert mvj.block_ref_linenum is None
