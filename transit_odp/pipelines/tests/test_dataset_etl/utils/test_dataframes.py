import pytest
from shapely.geometry import Point
import pandas as pd
import geopandas

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    DistrictFactory,
    LocalityFactory,
    StopPointFactory,
    FlexibleZoneFactory,
)
from transit_odp.naptan.models import AdminArea, FlexibleZone
from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    create_naptan_flexible_zone_df_from_queryset,
    create_flexible_zone_df,
    merge_vj_tracks_df,
)
from transit_odp.pipelines.tests.utils import check_frame_equal


pytestmark = pytest.mark.django_db


def test_create_naptan_flexible_zone_df_from_queryset():
    # setup
    admin_area = AdminAreaFactory()
    district = DistrictFactory()
    locality = LocalityFactory(admin_area=admin_area, district=district)
    naptan_stoppoint = StopPointFactory(locality=locality, admin_area=admin_area)
    FlexibleZoneFactory(naptan_stoppoint=naptan_stoppoint, sequence_number=1)
    FlexibleZoneFactory(naptan_stoppoint=naptan_stoppoint, sequence_number=2)

    qs = FlexibleZone.objects.all()

    # test
    df = create_naptan_flexible_zone_df_from_queryset(qs)
    columns_names = list(df.columns)
    assert len(df) == 1
    assert columns_names == ["naptan_id", "flexible_location"]
    
    
def test_merge_vj_tracks_df():
        # Setup
        tracks_data = {
            "rl_ref": [1, 2],
            "rs_ref": ["rs1", "rs2"],
            "rl_order": [1, 2],
            "id": [1, 2],
            "file_id": [1, 1],
        }
        vehicle_journeys_data = {
            "journey_pattern_ref": ["jp-1", "jp-2"],
            "id": [1, 2],
            "file_id": [1, 1],
        }
        tracks_map_data = {
            "jp_ref": ["1", "2"],
            "rs_ref": ["rs1", "rs2"],
            "rs_order": [1, 2],
            "file_id": [1, 1],
        }

        tracks_df = pd.DataFrame(tracks_data)
        vehicle_journeys_df = pd.DataFrame(vehicle_journeys_data)
        tracks_map_df = pd.DataFrame(tracks_map_data)

        # Test
        result_df = merge_vj_tracks_df(tracks_df, vehicle_journeys_df, tracks_map_df)

        # Expected result
        expected_data = {
            "rl_ref": [1, 2],
            "rs_ref": ["rs1", "rs2"],
            "tracks_id": [1, 2],
            "file_id": [1, 1],
            "jp_ref": ["1", "2"],
            "sequence": [0, 0],
            "vj_id": [1, 2],
        }
        expected_df = pd.DataFrame(expected_data)
        # add index to expected_df
        expected_df.reset_index(inplace=True)
        # order columns in expected_df
        expected_df = expected_df[["rl_ref", "rs_ref", "tracks_id", "file_id","index", "jp_ref", "sequence", "vj_id"]]

        # Assert
        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_rows", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_colwidth", None)
        print(result_df)
        print(expected_df)
        pd.testing.assert_frame_equal(result_df, expected_df)



