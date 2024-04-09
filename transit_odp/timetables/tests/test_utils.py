import os

import pandas as pd
import pytest
from django.core.files import File

from transit_odp.timetables.transxchange import TransXChangeDocument
from transit_odp.timetables.dataframes import (
    flexible_journey_patterns_to_dataframe,
    flexible_stop_points_from_journey_details,
)
from transit_odp.timetables.utils import (
    get_vehicle_journeys_operating_nonoperating,
    filter_df_serviced_org_operating,
    get_df_operating_vehicle_journey,
    get_df_timetable_visualiser,
)
from transit_odp.pipelines.tests.utils import check_frame_equal

# setup
cur_dir = os.path.abspath(os.path.dirname(__file__))

csv_file = "data/test_base_vehicle_journey.csv"
df_base_vehicle_journeys = pd.read_csv(os.path.join(cur_dir, csv_file))

csv_file = "data/test_operating_exception_vehicle_journey.csv"
df_op_exception_vehicle_journeys = pd.read_csv(os.path.join(cur_dir, csv_file))

csv_file = "data/test_nonoperating_exception_vehicle_journey.csv"
df_nonop_exception_vehicle_journeys = pd.read_csv(os.path.join(cur_dir, csv_file))

csv_file = "data/test_serviced_organisation_working_days.csv"
df_serviced_org_working_days = pd.read_csv(os.path.join(cur_dir, csv_file))

csv_file = "test_vehicle_journey_operating.csv"
df_vehicle_journey_operating = pd.read_csv(os.path.join(cur_dir, csv_file))


def test_get_vehicle_journeys_operating_nonoperating():
    """
    Test the get_vehicle_journeys_operating_nonoperating() based on
    different scenario
    """

    expected_op_vehicle_journeys = [363]
    expected_nonop_vehicle_journeys = [333]
    expected_all_vehicle_journeys = [363, 333]

    vehicle_journeys = get_vehicle_journeys_operating_nonoperating(
        df_op_exception_vehicle_journeys, df_nonop_exception_vehicle_journeys
    )

    # Scenario 1: Operating and non-operating dataframes are not empty
    assert isinstance(vehicle_journeys, tuple)  # Check the return type of the function
    assert len(vehicle_journeys) == 3  # Check the count of tuple returned
    assert len(expected_op_vehicle_journeys) == len(
        vehicle_journeys[0]
    )  # Compare the operating and non-operating vehicle journeys
    assert all(
        [a == b for a, b in zip(vehicle_journeys[0], expected_op_vehicle_journeys)]
    )
    assert all(
        [a == b for a, b in zip(vehicle_journeys[1], expected_nonop_vehicle_journeys)]
    )
    assert all(
        [a == b for a, b in zip(vehicle_journeys[2], expected_all_vehicle_journeys)]
    )

    # Scenario 2: Operating dataframe contains data and non-operating is empty
    vehicle_journeys = get_vehicle_journeys_operating_nonoperating(
        df_op_exception_vehicle_journeys, pd.DataFrame()
    )
    assert isinstance(vehicle_journeys, tuple)  # Check the return type of the function
    assert len(vehicle_journeys) == 3  # Check the count of tuple returned
    assert len(expected_op_vehicle_journeys) == len(
        vehicle_journeys[0]
    )  # Compare the operating vehicle journeys
    assert all(
        [a == b for a, b in zip(vehicle_journeys[0], expected_op_vehicle_journeys)]
    )
    assert len(vehicle_journeys[1]) == 0
    assert len(expected_op_vehicle_journeys) == len(vehicle_journeys[2])

    # Scenario 3: Operating dataframe is empty and non-operating contains data
    vehicle_journeys = get_vehicle_journeys_operating_nonoperating(
        pd.DataFrame(), df_nonop_exception_vehicle_journeys
    )
    assert isinstance(vehicle_journeys, tuple)  # Check the return type of the function
    assert len(vehicle_journeys) == 3  # Check the count of tuple returned
    assert len(vehicle_journeys[0]) == 0
    assert all(
        [a == b for a, b in zip(vehicle_journeys[1], expected_nonop_vehicle_journeys)]
    )
    assert len(expected_nonop_vehicle_journeys) == len(
        vehicle_journeys[1]
    )  # Compare the non-operating vehicle journeys
    assert len(expected_nonop_vehicle_journeys) == len(vehicle_journeys[2])


def test_get_df_operating_vehicle_journey():
    """
    Test the get_df_operating_vehicle_journey() based on target day
    """
    op_exception_vehicle_journeys = [
        363
    ]  # 363 vehicle journey id does not operate on Monday
    nonop_exception_vehicle_journeys = [333]  # 333 vehicle journey operates on Monday
    day_of_week = "Monday"

    actual_df_operating = get_df_operating_vehicle_journey(
        day_of_week,
        df_base_vehicle_journeys,
        op_exception_vehicle_journeys,
        nonop_exception_vehicle_journeys,
    )
    actual_vehicle_journey_operating = set(
        actual_df_operating["vehicle_journey_id"].unique()
    )
    # Scenario 1: Operating and non-operating dataframes are not empty
    assert isinstance(
        actual_df_operating, pd.DataFrame
    )  # Check the return type of the function
    assert all(
        [
            elem in actual_vehicle_journey_operating
            for elem in op_exception_vehicle_journeys
        ]
    )
    assert all(
        [
            elem not in actual_vehicle_journey_operating
            for elem in nonop_exception_vehicle_journeys
        ]
    )


def test_filter_df_serviced_org_operating():
    """
    Test the filter_df_serviced_org_operating() based on target date
    """
    target_date = "2023-01-09"
    all_exception_vehicle_journey = set([363, 333])
    expected_op_vehicle_journeys = [
        321,
        322,
        325,
        326,
        330,
        331,
        334,
        335,
        340,
        341,
        342,
        343,
        348,
        349,
        354,
        355,
    ]
    expected_nonop_vehicle_journeys = []

    serviced_org_vehicle_journeys = filter_df_serviced_org_operating(
        target_date, df_serviced_org_working_days, all_exception_vehicle_journey
    )
    assert isinstance(
        serviced_org_vehicle_journeys, tuple
    )  # Check the return type of the function
    assert len(serviced_org_vehicle_journeys) == 2
    assert len(expected_op_vehicle_journeys) == len(serviced_org_vehicle_journeys[0])
    assert len(expected_nonop_vehicle_journeys) == len(serviced_org_vehicle_journeys[1])


def test_get_df_timetable_visualiser():
    """
    Test the get_df_timetable_visualiser() based on target date
    """

    actual_df_vehicle_journey = get_df_timetable_visualiser(pd.DataFrame())
    assert actual_df_vehicle_journey.empty

    # TODO: Add more test cases based on the logic
