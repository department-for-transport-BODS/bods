from datetime import datetime
import pandas as pd
import pytest
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.tests.utils import (
    get_base_csv,
    get_serviced_org_csv,
)

pytestmark = pytest.mark.django_db

def test_timetable_visualier(mocker):
    revision_id = "1"
    service_code = "1"
    line = "11a"
    target_date = datetime.strptime("2024-05-13", "%Y-%m-%d")
    visualiser = TimetableVisualiser(revision_id, service_code, line, target_date)

    base_csv = get_base_csv(
        "transit_odp/pipelines/tests/test_dataset_etl/data/csv/with_vj_operating_profile_multi_serviced_org_base.csv"
    )

    serviced_org = get_serviced_org_csv(
        "transit_odp/pipelines/tests/test_dataset_etl/data/csv/with_vj_operating_profile_multi_serviced_org_so_data.csv"
    )
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
