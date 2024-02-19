import pandas as pd
from transit_odp.pipelines.pipelines.dataset_etl.utils.transform import transform_geometry

from shapely.geometry import Point


def test_transform_geometry():
    # setup
    input_dataframe = pd.DataFrame([{
        "bus_stop_type": "flexible",
        "geometry": Point(1, 0),
        "flexible_location": Point(1, 0),
    },
    {
        "bus_stop_type": "fixed_flexible",
        "geometry": Point(1, 0),
        "flexible_location": Point(1, 0),
    },
    {
        "bus_stop_type": "fixed_flexible",
        "geometry": Point(1, 0),
        "flexible_location": Point(1, 0),
    }])

    df = transform_geometry(input_dataframe)
    df_fixed_flexible = df[df['bus_stop_type'] == 'fixed_flexible']
    assert len(df) == 3
    assert isinstance(df_fixed_flexible.iloc[0]['geometry'], list) 
    
    
