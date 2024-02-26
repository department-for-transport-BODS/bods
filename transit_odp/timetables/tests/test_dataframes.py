import os

import pandas as pd
import pytest
from django.core.files import File

from transit_odp.timetables.transxchange import TransXChangeDocument
from transit_odp.timetables.dataframes import flexible_journey_patterns_to_dataframe
from transit_odp.pipelines.tests.utils import check_frame_equal


def test_flexible_journey_patterns_to_dataframe():
    # setup
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    test_file = "data/test_flexible_and_standard_service.xml"
    file_obj = File(os.path.join(cur_dir, test_file))
    doc = TransXChangeDocument(file_obj.file)

    services = doc.get_services()
    expected_stopoint_df = pd.DataFrame(
        [
            {
                "atco_code": "02903501",
                "bus_stop_type": "fixed_flexible",
                "journey_pattern_id": "PB0002032:467-jp_1",
                "service_code": "PB0002032:467",
                "direction": "outbound",
            },
            {
                "atco_code": "02901353",
                "bus_stop_type": "flexible",
                "journey_pattern_id": "PB0002032:467-jp_1",
                "service_code": "PB0002032:467",
                "direction": "outbound",
            },
            {
                "atco_code": "02901278",
                "bus_stop_type": "flexible",
                "journey_pattern_id": "UZ000WOCT:216-jp_2",
                "service_code": "UZ000WOCT:216",
                "direction": "outbound",
            },
        ]
    )
    # test
    stoppoint_df = flexible_journey_patterns_to_dataframe(services)
    assert check_frame_equal(stoppoint_df, expected_stopoint_df)
