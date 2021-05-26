import json
from pathlib import Path
from typing import Dict, Final

import geopandas as gpd
import pandas as pd
import pytest

from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.pipelines.pipelines.dqs_report_etl.utils import load_geojson

DATA_DIR: Final = Path(__file__).parent.joinpath("data")
SAMPLE_JSON: Final = DATA_DIR.joinpath("yorkshire_warnings_sample.json")
SAMPLE_TXC: Final = DATA_DIR.joinpath("ea_20-1A-A-y08-1.xml")


@pytest.fixture()
def sample_report() -> Dict:
    with SAMPLE_JSON.open("r") as fin:
        return json.load(fin)


@pytest.fixture()
def report() -> DataQualityReportFactory:
    return DataQualityReportFactory(file__from_path=str(SAMPLE_JSON))


@pytest.fixture()
def txc_report() -> DataQualityReportFactory:
    return DataQualityReportFactory(
        file__from_path=str(SAMPLE_JSON),
        revision__upload_file__from_path=str(SAMPLE_TXC),
    )


@pytest.fixture()
def stops_df() -> gpd.GeoDataFrame:
    df = load_geojson(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "id": "0",
                    "type": "Feature",
                    "properties": {
                        "atco_code": "300000492FZ",
                        "bearing": 8,
                        "feature_name": "Demand Responsive Area",
                        "type": "BCT",
                        "synthetic": False,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": (-1.1372773238238423, 52.346655194010665),
                    },
                },
                {
                    "id": "1",
                    "type": "Feature",
                    "properties": {
                        "atco_code": "0600CR19133",
                        "bearing": 2,
                        "feature_name": "Station View (E-bound)",
                        "type": "BCT",
                        "synthetic": True,
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": (-2.518177475249135, 53.063122731640604),
                    },
                },
            ],
        }
    )
    df = df.rename(columns={"id": "ito_id", "feature_name": "name"}).set_index("ito_id")
    return df


@pytest.fixture()
def lines_df() -> pd.DataFrame:
    df = pd.DataFrame(
        [
            {"id": "LI0", "name": "CB3:Roos - Bilton"},
            {"id": "LI1", "name": "GT:Goole - Old Goole"},
            {"id": "LI2", "name": "4:Boroughbridge - Skelton on Ure"},
            {"id": "LI3", "name": "5A:Strensall - Acomb"},
            {"id": "LI4", "name": "6:Minskip - Bishopton"},
        ]
    )
    df = df.rename(columns={"id": "ito_id"}).set_index("ito_id")
    return df
