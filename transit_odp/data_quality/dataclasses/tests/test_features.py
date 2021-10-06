from datetime import time

import pytest

from transit_odp.data_quality.dataclasses.factories import VehicleJourneyFactory


@pytest.mark.parametrize(
    ("start", "expected"), [(300, time(0, 5)), (-300, time(23, 55))]
)
def test_vehicle_journey_start_time(start, expected):
    vehicle_journey = VehicleJourneyFactory(start=start)
    assert vehicle_journey.start_time == expected
