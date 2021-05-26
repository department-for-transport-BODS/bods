from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

import transit_odp.pipelines.pipelines.dqs_report_etl.utils
from transit_odp.data_quality.etl import TransXChangeDQPipeline
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.models.warnings import IncorrectNOCWarning
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.pipelines.pipelines.dqs_report_etl import extract
from transit_odp.pipelines.tests.utils import assert_frame_equal_basic

DATA_DIR = Path(__file__).parent.joinpath("data")
TXCFILE = DATA_DIR.joinpath("ea_20-1A-A-y08-1.xml")
ZIPFILE = DATA_DIR.joinpath("EA_TXC_5_files.zip")

pytestmark = pytest.mark.django_db


def test_extract(txc_report, mocker):
    mocked_model = mocker.Mock()
    mocker.patch.object(extract, "extract_model", return_value=mocked_model)

    mocked_warnings = mocker.Mock()
    mocker.patch.object(extract, "extract_warnings", return_value=mocked_warnings)

    extracted = extract.run(txc_report.id)

    assert extracted.report == txc_report
    assert extracted.model == mocked_model
    assert extracted.warnings == mocked_warnings


def test_extract_model(sample_report):
    def from_geojson(geojson, columns=None) -> gpd.GeoDataFrame:
        # There is a 'bug' in from_features which causes the 'id' of the
        # feature to not be included in the df.
        # This causes an issue here as service_links doesn't define 'id'
        # within the properties but in the feature object
        # (the correct place). The code handles this properly in both cases.
        df = gpd.GeoDataFrame.from_features(geojson, columns=columns)
        df["id"] = [f["id"] for f in geojson["features"]]
        return df.rename(columns={"id": "ito_id", "feature_name": "name"}).set_index(
            "ito_id"
        )

    model = sample_report["model"]

    expected_lines = (
        pd.DataFrame(model["lines"], columns=["id", "name"])
        .rename(columns={"id": "ito_id"})
        .set_index("ito_id")
    )
    expected_timing_patterns = (
        pd.DataFrame(
            model["timing_patterns"],
            columns=["id", "service_pattern", "timings", "vehicle_journeys"],
        )
        .rename(columns={"id": "ito_id", "service_pattern": "service_pattern_ito_id"})
        .set_index("ito_id")
    )
    expected_vehicle_journeys = (
        pd.DataFrame(
            model["vehicle_journeys"],
            columns=["id", "timing_pattern", "start", "feature_name", "dates"],
        )
        .rename(
            columns={
                "id": "ito_id",
                "feature_name": "name",
                "timing_pattern": "timing_pattern_ito_id",
            }
        )
        .set_index("ito_id")
    )
    expected_service_patterns = from_geojson(
        model["service_patterns"],
        columns=[
            "id",
            "geometry",
            "feature_name",
            "length_m",
            "line",
            "stops",
            "timing_patterns",
            "service_links",
        ],
    )
    expected_service_links = from_geojson(
        model["service_links"],
        columns=["geometry", "feature_name", "from_stop", "length_m", "to_stop"],
    )
    expected_stops = from_geojson(
        model["stops"],
        columns=[
            "id",
            "geometry",
            "atco_code",
            "bearing",
            "feature_name",
            "type",
            "synthetic",
        ],
    )

    extracted = extract.extract_model(sample_report)

    assert_frame_equal_basic(extracted.stops, expected_stops)
    assert_frame_equal_basic(extracted.lines, expected_lines)
    assert_frame_equal_basic(extracted.service_patterns, expected_service_patterns)
    assert_frame_equal_basic(extracted.service_links, expected_service_links)
    assert_frame_equal_basic(extracted.timing_patterns, expected_timing_patterns)
    assert_frame_equal_basic(extracted.vehicle_journeys, expected_vehicle_journeys)


def test_load_geojson():
    geojson = {
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
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": (-2.518177475249135, 53.063122731640604),
                },
            },
        ],
    }

    expected = gpd.GeoDataFrame.from_features(
        geojson, columns=["atco_code", "geometry"]
    )
    expected["id"] = ["0", "1"]

    columns = ["id", "atco_code", "geometry"]
    actual = transit_odp.pipelines.pipelines.dqs_report_etl.utils.load_geojson(
        geojson, columns
    )

    assert_frame_equal_basic(actual, expected)


class TestExtractIncorrectNocWarnings:
    def test_extract(self):
        organisation = OrganisationFactory(nocs=["XYZ"])
        report = DataQualityReportFactory(
            revision__dataset__organisation=organisation,
            revision__upload_file__from_path=str(TXCFILE),
        )
        pipeline = TransXChangeDQPipeline(report)
        pipeline.extract()
        pipeline.create_incorrect_nocs_warning()
        warning = IncorrectNOCWarning.objects.get(report_id=report.id, noc="DEWS")
        assert warning.report_id == report.id
        assert warning.noc == "DEWS"

    @pytest.mark.parametrize(
        "filepath,expected",
        [(TXCFILE, ["DEWS"]), (ZIPFILE, ["DEWS"])],
    )
    def test_process_file(self, filepath, expected):
        report = DataQualityReportFactory(
            revision__upload_file__from_path=str(filepath),
        )
        pipeline = TransXChangeDQPipeline(report)
        extract = pipeline.extract()
        assert extract.nocs == expected
