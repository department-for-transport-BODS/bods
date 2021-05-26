from typing import Dict, Union

import geopandas as gpd
from shapely.geometry import shape


def load_geojson(
    features: Dict,
    columns=None,
    crs: Union[str, Dict] = "epsg:4326",
    *args,
    **kwargs,
):
    def inner(features_lst):
        for feature in features_lst:
            props = feature["properties"]
            props.update(
                {
                    "geometry": shape(feature["geometry"])
                    if feature["geometry"]
                    else None
                }
            )
            if "id" in feature:
                props.update({"id": feature["id"]})
            yield props

    if isinstance(features, dict) and features.get("type") == "FeatureCollection":
        features_lst = features["features"]
    else:
        features_lst = features

    return gpd.GeoDataFrame(
        inner(features_lst), columns=columns, crs=crs, *args, **kwargs
    )
