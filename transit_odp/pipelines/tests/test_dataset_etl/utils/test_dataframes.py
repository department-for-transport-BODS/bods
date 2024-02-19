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
    print(f"df.columns: {df.columns}")
    assert len(df) == 1
    assert columns_names == ["naptan_id", "flexible_location"]
