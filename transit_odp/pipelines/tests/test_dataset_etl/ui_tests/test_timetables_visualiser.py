from datetime import datetime
import pandas as pd
import pytest
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.tests.utils import (
    get_base_csv,
    get_csv,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "line, target_date, folder_path",
    [
        ("11a", "2024-05-13", "day_of_week_operational"),
        ("7", "2024-09-10", "day_of_week_non_operational_so"),
        ("7", "2024-01-09", "day_of_week_operational_so"),
        ("11a", "2024-05-27", "target_date_op_non_exception"),
        ("11a", "2024-05-06", "target_date_op_exception"),
        ("101", "2024-05-17", "with_holidays_day_of_week_operational"),
        ("101", "2024-05-27", "with_holidays_target_date_op_exceptions"),
        ("101", "2024-05-06", "with_holidays_target_date_non_op_exceptions"),
    ],
)
def test_timetable_visualiser_day_of_week(mocker, line, target_date, folder_path):
    revision_id = "1"
    service_code = "1"
    target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    visualiser = TimetableVisualiser(revision_id, service_code, line, target_date)

    base_csv = get_base_csv(
        f"transit_odp/pipelines/tests/test_dataset_etl/data/csv/{folder_path}/with_vj_operating_profile_multi_serviced_org_base.csv"
    )
    serviced_org = get_csv(
        f"transit_odp/pipelines/tests/test_dataset_etl/data/csv/{folder_path}/with_vj_operating_profile_multi_serviced_org_so_data.csv",
        date_columns=["start_date", "end_date"],
    )
    op_exceptions = get_csv(
        f"transit_odp/pipelines/tests/test_dataset_etl/data/csv/{folder_path}/with_vj_operating_profile_multi_serviced_org_op_excep.csv",
        date_columns=["operating_date"],
    )
    non_op_exceptions = get_csv(
        f"transit_odp/pipelines/tests/test_dataset_etl/data/csv/{folder_path}/with_vj_operating_profile_multi_serviced_org_non_op_excep.csv",
        date_columns=["non_operating_date"],
    )
    inbound_csv = pd.read_csv(
        f"transit_odp/pipelines/tests/test_dataset_etl/data/csv/{folder_path}/with_vj_operating_profile_multi_serviced_org_inbound_final.csv"
    )
    outbound_csv = pd.read_csv(
        f"transit_odp/pipelines/tests/test_dataset_etl/data/csv/{folder_path}/with_vj_operating_profile_multi_serviced_org_outbound_final.csv"
    )
    mocker.patch.multiple(
        visualiser,
        get_df_base_journeys=mocker.Mock(return_value=base_csv),
        get_df_servicedorg_vehicle_journey=mocker.Mock(return_value=serviced_org),
        get_df_nonop_exceptions_vehicle_journey=mocker.Mock(
            return_value=non_op_exceptions
        ),
        get_df_op_exceptions_vehicle_journey=mocker.Mock(return_value=op_exceptions),
    )

    timetables = visualiser.get_timetable_visualiser()

    pd.testing.assert_frame_equal(inbound_csv, timetables["inbound"]["df_timetable"])
    pd.testing.assert_frame_equal(outbound_csv, timetables["outbound"]["df_timetable"])
