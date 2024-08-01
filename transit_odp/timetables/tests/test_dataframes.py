import os

import pandas as pd
import pytest
from django.core.files import File
from django.contrib.gis.geos import Point, Polygon

from transit_odp.timetables.transxchange import TransXChangeDocument
from transit_odp.timetables.dataframes import (
    flexible_journey_patterns_to_dataframe,
    flexible_stop_points_from_journey_details,
    provisional_stops_to_dataframe,
)
from transit_odp.pipelines.tests.utils import check_frame_equal
from transit_odp.transmodel.models import StopActivity

pytestmark = pytest.mark.django_db


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
                "activity_id": 1,
            },
            {
                "atco_code": "02901353",
                "bus_stop_type": "flexible",
                "journey_pattern_id": "PB0002032:467-jp_1",
                "service_code": "PB0002032:467",
                "direction": "outbound",
                "activity_id": 1,
            },
            {
                "atco_code": "02901278",
                "bus_stop_type": "flexible",
                "journey_pattern_id": "UZ000WOCT:216-jp_2",
                "service_code": "UZ000WOCT:216",
                "direction": "outbound",
                "activity_id": 1,
            },
        ]
    )
    # test
    stop_activities = StopActivity.objects.all()
    stoppoint_df = flexible_journey_patterns_to_dataframe(services, stop_activities)
    assert check_frame_equal(stoppoint_df, expected_stopoint_df)


def test_flexible_journey_patterns():
    # setup
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    test_file = "data/test_flexiblezones_tag_fixedstop_tag.xml"
    file_obj = File(os.path.join(cur_dir, test_file))
    doc = TransXChangeDocument(file_obj.file)

    services = doc.get_services()
    expected_stopoint_df = pd.DataFrame(
        [
            {
                "atco_code": "030058880001",
                "bus_stop_type": "flexible",
                "journey_pattern_id": "PF0000508:11-jp_1",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
            {
                "atco_code": "030058860001",
                "bus_stop_type": "flexible",
                "journey_pattern_id": "PF0000508:11-jp_1",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
            {
                "atco_code": "030058920001",
                "bus_stop_type": "fixed_flexible",
                "journey_pattern_id": "PF0000508:11-jp_1",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
            {
                "atco_code": "030058870001",
                "bus_stop_type": "fixed_flexible",
                "journey_pattern_id": "PF0000508:11-jp_1",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
        ]
    )
    # test
    stop_activities = StopActivity.objects.all()
    stoppoint_df = flexible_journey_patterns_to_dataframe(services, stop_activities)
    assert check_frame_equal(stoppoint_df, expected_stopoint_df)


def test_flexible_stop_points_from_journey_details():
    # setup
    flexible_journey_pattern_details = pd.DataFrame(
        [
            {
                "file_id": "339cfb45-3123-4828-8f60-28489f5646cc",
                "journey_pattern_id": "PF0000508:11-jp_1",
                "atco_code": "030058880001",
                "bus_stop_type": "flexible",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
            {
                "file_id": "339cfb45-3123-4828-8f60-28489f5646cc",
                "journey_pattern_id": "PF0000508:11-jp_1",
                "atco_code": "030058860001",
                "bus_stop_type": "flexible",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
            {
                "file_id": "339cfb45-3123-4828-8f60-28489f5646cc",
                "journey_pattern_id": "PF0000508:11-jp_1",
                "atco_code": "030058920001",
                "bus_stop_type": "fixed_flexible",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
            {
                "file_id": "339cfb45-3123-4828-8f60-28489f5646cc",
                "journey_pattern_id": "PF0000508:11-jp_2",
                "atco_code": "030058870001",
                "bus_stop_type": "fixed_flexible",
                "service_code": "PF0000508:11",
                "direction": "outbound",
                "activity_id": 1,
            },
        ]
    )

    expected_stopoint_df = pd.DataFrame(
        [
            {"atco_code": "030058880001", "bus_stop_type": "flexible"},
            {"atco_code": "030058860001", "bus_stop_type": "flexible"},
            {"atco_code": "030058920001", "bus_stop_type": "fixed_flexible"},
            {"atco_code": "030058870001", "bus_stop_type": "fixed_flexible"},
        ]
    ).set_index("atco_code")

    # test
    stop_points = flexible_stop_points_from_journey_details(
        flexible_journey_pattern_details
    )
    assert check_frame_equal(stop_points, expected_stopoint_df)


def test_provisional_stops_to_dataframe():
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    test_file = "data/grid_wsg84_stoppoints.xml"
    file_obj = File(os.path.join(cur_dir, test_file))
    doc = TransXChangeDocument(file_obj.file)
    stoppoints = doc.get_stop_points()

    stoppoints_df = provisional_stops_to_dataframe(stoppoints, doc)

    expected_stoppoint_df = pd.DataFrame(
        [
            {
                "atco_code": "999014AA766B",
                "locality": "E0047158",
                "common_name": "Dover (DFDS Ferry)",
            },
            {
                "atco_code": "999020B022A8",
                "locality": "E0047176",
                "common_name": "Calais (Irish Ferries)",
            },
            {
                "atco_code": "99905B2A7B8E",
                "locality": "N0072556",
                "common_name": "Birmingham Summer Row- Great Charles Street",
            },
            {
                "atco_code": "9990A0A50227",
                "locality": "E0000819",
                "common_name": "Cambridge (Trumpington Park and Ride)",
            },
            {
                "atco_code": "9990DCC13E03",
                "locality": "E0047176",
                "common_name": "Calais (P&O Ferry)",
            },
            {
                "atco_code": "9990DCC31F56",
                "locality": "E0015221",
                "common_name": "Folkestone (Eurotunnel)",
            },
            {
                "atco_code": "9990DCC32234",
                "locality": "E0047176",
                "common_name": "Calais (Eurotunnel)",
            },
            {
                "atco_code": "9990DCC5426B",
                "locality": "E0015176",
                "common_name": "Paris (Bercy Seine)",
            },
            {
                "atco_code": "9990DCC54F0B",
                "locality": "E0047158",
                "common_name": "Dover (P&O Ferry)",
            },
            {
                "atco_code": "9990DD0464FB",
                "locality": "E0047158",
                "common_name": "Dover (Irish Ferries)",
            },
            {
                "atco_code": "9990EEEA5A9B",
                "locality": "E0047176",
                "common_name": "Calais (DFDS Ferry)",
            },
        ]
    ).set_index("atco_code")
    stoppoints_df.drop(columns=["geometry"], inplace=True)
    assert check_frame_equal(stoppoints_df, expected_stoppoint_df)
