import os
from pathlib import PurePath

import pandas as pd
import pytest

from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.models import (
    Service,
    ServiceLink,
    ServicePattern,
    ServicePatternServiceLink,
    ServicePatternStop,
    StopPoint,
    TimingPattern,
    TimingPatternStop,
    VehicleJourney,
)
from transit_odp.pipelines.pipelines.dqs_report_etl import extract, transform_model
from transit_odp.pipelines.tests.utils import assert_frame_equal_basic

FILE_DIR = os.path.abspath(os.path.dirname(__file__))

DATA_DIR = PurePath(__file__).parent.joinpath("data")
TXCFILE = str(DATA_DIR.joinpath("ea_20-1A-A-y08-1.xml"))

pytestmark = pytest.mark.django_db


def test_transform_stops(stops_df):
    # Test
    transformed = transform_model.transform_stops(stops_df)

    # Assert
    assert set(transformed.columns) == {
        "atco_code",
        "synthetic",
        "geometry",
        "bearing",
        "name",
        "type",
        "id",
    }
    assert transformed.index.name == "ito_id"

    # Join created StopPoints onto input stops_df and check if it matches transformed
    stops = pd.DataFrame(StopPoint.objects.values("id", "ito_id")).set_index("ito_id")
    expected = stops_df.join(stops)

    assert_frame_equal_basic(transformed, expected)


def test_transform_lines(lines_df):
    # Setup
    report = DataQualityReportFactory()

    # Test
    transformed = transform_model.transform_lines(report, lines_df)

    # Assert
    assert set(transformed.columns) == {"id", "name"}
    assert transformed.index.name == "ito_id"

    # Assert report has services
    assert report.services.count() == len(lines_df)

    # Get created services
    services = pd.DataFrame(Service.objects.values("id", "name"))

    # Note we merge on 'name' here since Service doesn't store the 'ito_id'
    # column and we know its unique here.
    # The code under test merges by row index, so would avoid the problem
    # if 'name' is not unique.
    expected = (
        lines_df.reset_index()
        .merge(services, how="left", on="name")
        .set_index(lines_df.index.name)
    )

    assert_frame_equal_basic(transformed, expected)


def test_transform_service_links(report):
    # Setup
    testfile = os.path.join(FILE_DIR, "data/service-link-missing-stops.json")
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    extracted = extract.run(report.id)

    # Transform stops
    stops = transform_model.transform_stops(extracted.model.stops)

    # Test
    transformed = transform_model.transform_service_links(
        extracted.model.service_links, stops
    )

    # Assert
    assert set(transformed.columns) == {
        "id",
        "name",
        "geometry",
        "length_m",
        "from_stop",
        "to_stop",
        "from_stop_id",
        "to_stop_id",
    }
    assert transformed.index.name == "ito_id"
    assert ServiceLink.objects.count() == len(extracted.model.service_links)


@pytest.mark.parametrize(
    "filename",
    (
        "timing-first.json",
        "timing-last.json",
        "timing-fast.json",
    ),
)
def test_transform_timing_patterns(filename):
    # Setup

    testfile = os.path.join(FILE_DIR, "data/" + filename)
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    extracted = extract.run(report.id)

    # transform other data
    transform_model.transform_stops(extracted.model.stops)
    services = transform_model.transform_lines(report, extracted.model.lines)
    service_patterns = transform_model.transform_service_patterns(
        services, extracted.model.service_patterns
    )

    # Test
    transformed = transform_model.transform_timing_patterns(
        service_patterns, extracted.model.timing_patterns
    )

    # Assert
    assert set(transformed.columns) == {
        "id",
        "service_pattern_id",
        "service_pattern_ito_id",
        "timings",
        "vehicle_journeys",
    }
    assert transformed.index.name == "ito_id"
    assert TimingPattern.objects.count() == len(extracted.model.timing_patterns)


# Utils


def test_bulk_create_stoppoints(stops_df):
    # Setup
    # Test
    stops = transform_model.bulk_create_stoppoints(stops_df)

    # Assert
    assert len(stops) == 2
    assert {stop.atco_code for stop in stops} == {"300000492FZ", "0600CR19133"}
    for stop in stops:
        if stop.atco_code == "300000492FZ":
            assert stop.name == "Demand Responsive Area"
            assert stop.type == "BCT"
            assert stop.bearing == 8
            assert (stop.geometry.x, stop.geometry.y) == (
                -1.1372773238238423,
                52.346655194010665,
            )
        else:
            assert stop.name == "Station View (E-bound)"
            assert stop.type == "BCT"
            assert stop.bearing == 2
            assert (stop.geometry.x, stop.geometry.y) == (
                -2.518177475249135,
                53.063122731640604,
            )


def test_bulk_create_services(report, lines_df):
    """
    Tests Services are created from the DataFrame.

    Should return created services in the same order as the input DataFrame
    """
    # Test
    services = transform_model.bulk_create_services(lines_df)

    # Assert
    assert len(services) == len(lines_df) == Service.objects.count()

    # Assert services are in the same order as lines_df
    for i, record in enumerate(lines_df.itertuples()):
        assert services[i].name == record.name
