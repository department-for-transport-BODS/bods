from datetime import datetime
from unittest.mock import patch
import pandas as pd
import pytest
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.transmodel.factories import (
    ServiceFactory,
    ServicePatternFactory,
    ServiceServicePatternFactory,
)

import os

pytestmark = pytest.mark.django_db


def modify_time_columns(df: pd.DataFrame, time_columns: list):
    for col in time_columns:
        df[col] = pd.to_datetime(df[col], format="%H:%M:%S")
        df[col] = df[col].dt.time

    return df


def modify_date_columns(df: pd.DataFrame, date_columns: list):
    for col in date_columns:
        df[col] = pd.to_datetime(df[col])
    return df


def test_timetable_visualier(mocker):
    revision_id = "8066"
    service_code = "1"
    line = "11a"
    target_date = datetime.strptime("2024-05-13", "%Y-%m-%d")
    visualiser = TimetableVisualiser(revision_id, service_code, line, target_date)
    base_csv = pd.read_csv("base.csv")
    date_columns = ["start_date", "end_date"]
    base_csv = modify_date_columns(base_csv, date_columns)
    base_csv["departure_time"] = pd.to_datetime(
        base_csv["departure_time"], format="%H:%M:%S"
    )
    base_csv["departure_time"] = base_csv["departure_time"].dt.time

    serviced_org = pd.read_csv(
        "transit_odp/pipelines/tests/test_dataset_etl/data/csv/with_vj_operating_profile_multi_serviced_org_so_data.csv"
    )
    serviced_org = modify_date_columns(serviced_org, date_columns)
    inbound_csv = pd.read_csv(
        "transit_odp/pipelines/tests/test_dataset_etl/data/csv/with_vj_operating_profile_multi_serviced_org_inbound_final.csv"
    )
    outbound_csv = pd.read_csv(
        "transit_odp/pipelines/tests/test_dataset_etl/data/csv/with_vj_operating_profile_multi_serviced_org_outbound_final.csv"
    )
    mocker.patch.multiple(
        visualiser,
        get_df_base_journeys=mocker.Mock(return_value=base_csv),
        get_df_servicedorg_vehicle_journey=mocker.Mock(return_value=serviced_org),
    )

    timetables = visualiser.get_timetable_visualiser()

    pd.testing.assert_frame_equal(inbound_csv, timetables["inbound"]["df_timetable"])
    pd.testing.assert_frame_equal(outbound_csv, timetables["outbound"]["df_timetable"])
