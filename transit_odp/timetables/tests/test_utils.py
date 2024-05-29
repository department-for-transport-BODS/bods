import os
import pandas as pd
from transit_odp.timetables.utils import (
    get_filtered_rows_by_journeys,
    get_journey_mappings,
    get_vehicle_journeyids_exceptions,
    get_non_operating_vj_serviced_org,
    get_df_operating_vehicle_journey,
    get_df_timetable_visualiser,
    get_vehicle_journey_codes_sorted,
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

csv_file = "data/test_operating_vehicle_journey.csv"
df_vehicle_journey_operating = pd.read_csv(os.path.join(cur_dir, csv_file))

csv_file = "data/test_timetable_visualiser.csv"
expected_df_timetable_visualiser = pd.read_csv(
    os.path.join(cur_dir, csv_file), index_col=0
)

csv_file = "data/test_input_filter_row_journeys.csv"
df_input_operating_profiles = pd.read_csv(os.path.join(cur_dir, csv_file), index_col=0)

csv_file = "data/test_output_filter_row_journeys.csv"
df_output_operating_profiles = pd.read_csv(os.path.join(cur_dir, csv_file), index_col=0)


def test_get_vehicle_journeys_operating_nonoperating():
    """
    Test the get_vehicle_journeys_operating_nonoperating() based on
    different scenario
    """

    expected_op_vehicle_journeys = [363]
    expected_nonop_vehicle_journeys = [333]

    vehicle_journeys = get_vehicle_journeyids_exceptions(
        df_op_exception_vehicle_journeys, df_nonop_exception_vehicle_journeys
    )

    # Scenario 1: Operating and non-operating dataframes are not empty
    assert isinstance(vehicle_journeys, tuple)  # Check the return type of the function
    assert len(vehicle_journeys) == 2  # Check the count of tuple returned
    assert len(expected_op_vehicle_journeys) == len(
        vehicle_journeys[0]
    )  # Compare the operating and non-operating vehicle journeys
    assert all(
        [a == b for a, b in zip(vehicle_journeys[0], expected_op_vehicle_journeys)]
    )
    assert all(
        [a == b for a, b in zip(vehicle_journeys[1], expected_nonop_vehicle_journeys)]
    )

    # Scenario 2: Operating dataframe contains data and non-operating is empty
    vehicle_journeys = get_vehicle_journeyids_exceptions(
        df_op_exception_vehicle_journeys, pd.DataFrame()
    )
    assert isinstance(vehicle_journeys, tuple)  # Check the return type of the function
    assert len(vehicle_journeys) == 2  # Check the count of tuple returned
    assert len(expected_op_vehicle_journeys) == len(
        vehicle_journeys[0]
    )  # Compare the operating vehicle journeys
    assert all(
        [a == b for a, b in zip(vehicle_journeys[0], expected_op_vehicle_journeys)]
    )
    assert len(vehicle_journeys[1]) == 0

    # Scenario 3: Operating dataframe is empty and non-operating contains data
    vehicle_journeys = get_vehicle_journeyids_exceptions(
        pd.DataFrame(), df_nonop_exception_vehicle_journeys
    )
    assert isinstance(vehicle_journeys, tuple)  # Check the return type of the function
    assert len(vehicle_journeys) == 2  # Check the count of tuple returned
    assert len(vehicle_journeys[0]) == 0
    assert all(
        [a == b for a, b in zip(vehicle_journeys[1], expected_nonop_vehicle_journeys)]
    )
    # Compare the non-operating vehicle journeys
    assert len(expected_nonop_vehicle_journeys) == len(vehicle_journeys[1])


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

    # Scenario 1: When the target date is between the non-operating journeys
    target_date = "2023-01-09"
    expected_nonop_vehicle_journeys = [541, 545, 549, 554, 560, 562, 567, 574]
    actual_nonop_vehicle_journeys = get_non_operating_vj_serviced_org(
        target_date, df_serviced_org_working_days
    )

    # Check the return type, length and list values
    assert isinstance(actual_nonop_vehicle_journeys, list)
    assert len(expected_nonop_vehicle_journeys) == len(actual_nonop_vehicle_journeys)
    assert expected_nonop_vehicle_journeys == actual_nonop_vehicle_journeys

    # Scenario 2: When the target date is less than start date for all vehicle journeys
    target_date = "2001-01-01"
    expected_nonop_vehicle_journeys = [540, 544, 550, 553, 559, 561, 568, 573]
    actual_nonop_vehicle_journeys = get_non_operating_vj_serviced_org(
        target_date, df_serviced_org_working_days
    )

    # Check the return type, length and list values
    assert isinstance(actual_nonop_vehicle_journeys, list)
    assert len(expected_nonop_vehicle_journeys) == len(actual_nonop_vehicle_journeys)
    assert expected_nonop_vehicle_journeys == actual_nonop_vehicle_journeys

    # Scenario 3: When the target date is greater than end date for all vehicle journeys
    target_date = "2030-01-01"
    expected_nonop_vehicle_journeys = [540, 544, 550, 553, 559, 561, 568, 573]
    actual_nonop_vehicle_journeys = get_non_operating_vj_serviced_org(
        target_date, df_serviced_org_working_days
    )

    # Check the return type, length and list values
    assert isinstance(actual_nonop_vehicle_journeys, list)
    assert len(expected_nonop_vehicle_journeys) == len(actual_nonop_vehicle_journeys)
    assert expected_nonop_vehicle_journeys == actual_nonop_vehicle_journeys

    # Scenario 4: When the target date is between the date ranges of the operating vehicle journeys
    target_date = "2022-07-27"
    expected_nonop_vehicle_journeys = [540, 544, 550, 553, 559, 561, 568, 573]
    # [540, 541, 544, 545, 549, 550, 553, 554, 559, 560, 561, 562, 567, 568, 573, 574]
    actual_nonop_vehicle_journeys = get_non_operating_vj_serviced_org(
        target_date, df_serviced_org_working_days
    )

    # Check the return type, length and list values
    assert isinstance(actual_nonop_vehicle_journeys, list)
    assert len(expected_nonop_vehicle_journeys) == len(actual_nonop_vehicle_journeys)
    assert expected_nonop_vehicle_journeys == actual_nonop_vehicle_journeys


def test_get_df_timetable_visualiser():
    """
    Test the get_df_timetable_visualiser() based on target date
    """

    actual_df_vehicle_journey, _ = get_df_timetable_visualiser(pd.DataFrame())
    assert actual_df_vehicle_journey.empty

    df_vehicle_journey_operating["departure_time"] = pd.to_datetime(
        df_vehicle_journey_operating["departure_time"], format="%H:%M:%S"
    ).dt.time
    actual_df_vehicle_journey, _ = get_df_timetable_visualiser(
        df_vehicle_journey_operating
    )

    # Check the dataframe expected
    assert check_frame_equal(
        actual_df_vehicle_journey, expected_df_timetable_visualiser.reset_index()
    )


def test_get_vehicle_journey_codes_sorted():
    """
    Test the get_vehicle_journey_codes_sorted() based on the vehicle journey operating
    """
    expected_vehicle_journey_ids = [
        ("6001", 540),
        ("6009", 544),
        ("6013", 547),
        ("6017", 550),
        ("6019", 552),
        ("6021", 553),
        ("6025", 555),
        ("6029", 556),
        ("6033", 557),
        ("6037", 558),
        ("6041", 559),
        ("6045", 561),
        ("6049", 563),
        ("6053", 564),
        ("6057", 565),
        ("6061", 566),
        ("6069", 568),
        ("6073", 569),
        ("6075", 571),
        ("6077", 573),
        ("6081", 577),
        ("6085", 579),
        ("6093", 580),
    ]
    # Check the vehicle journey ids
    actual_vehicle_journey_ids = get_vehicle_journey_codes_sorted(
        df_vehicle_journey_operating
    )
    assert expected_vehicle_journey_ids == actual_vehicle_journey_ids


def test_filter_rows_by_journeys():
    df_input_operating_profiles["exceptions_date"] = pd.to_datetime(
        df_input_operating_profiles["exceptions_date"]
    )
    df_output_operating_profiles["exceptions_date"] = pd.to_datetime(
        df_output_operating_profiles["exceptions_date"]
    )

    journey_mapping = get_journey_mappings(df_input_operating_profiles)
    filtered_data = get_filtered_rows_by_journeys(
        df_input_operating_profiles, journey_mapping
    )

    pd.testing.assert_frame_equal(filtered_data, df_output_operating_profiles)
