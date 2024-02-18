import pytest
from shapely.geometry import Point
import pandas as pd

import transit_odp.naptan.factories as naptan_factory
from transit_odp.naptan.models import AdminArea, FlexibleZone
from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import create_naptan_flexible_zone_df_from_queryset
from transit_odp.pipelines.tests.utils import check_frame_equal


pytestmark = pytest.mark.django_db


def test_create_naptan_flexible_zone_df_from_queryset():
    # setup
    admin_area = naptan_factory.AdminAreaFactory()
    district = naptan_factory.DistrictFactory()
    locality = naptan_factory.LocalityFactory(admin_area=admin_area, district=district)
    naptan_stoppoint = naptan_factory.StopPointFactory(locality=locality, admin_area=admin_area)
    naptan_factory.FlexibleZoneFactory(naptan_stoppoint=naptan_stoppoint, sequence_number=1)
    naptan_factory.FlexibleZoneFactory(naptan_stoppoint=naptan_stoppoint, sequence_number=2)
    
    qs = FlexibleZone.objects.all()
    
    # test
    df = create_naptan_flexible_zone_df_from_queryset(qs)
    columns_names = list(df.columns)
    print(f"df.columns: {df.columns}")
    assert len(df) == 1
    assert columns_names == ["naptan_id", "flexible_location"]


    
