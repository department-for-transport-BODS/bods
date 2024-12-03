import json
import os
from pathlib import PurePath

import pytest
from dateutil.parser import parse

from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.models import (
    JourneyDateRangeBackwardsWarning,
    JourneyStopInappropriateWarning,
    JourneyWithoutHeadsignWarning,
    ServiceLink,
    ServicePattern,
    StopPoint,
    TimingDropOffWarning,
    TimingPattern,
    TimingPatternStop,
    TimingPickUpWarning,
    VehicleJourney,
)
from transit_odp.pipelines.pipelines.dqs_report_etl import (
    extract,
    transform_model,
    transform_warnings,
)

FILE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = PurePath(__file__).parent.joinpath("data")
TXCFILE = str(DATA_DIR.joinpath("ea_20-1A-A-y08-1.xml"))


pytestmark = pytest.mark.django_db


def test_transform_timing_pick_up():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/timing-pick_up.json")
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    # get data from report
    with report.file.open("r") as fin:
        data = json.load(fin)["warnings"][0]
        data["warning_type"].replace("-", "_")
        warning_json = data["values"][0]

    extracted = extract.run(report.id)
    model = transform_model.run(extracted)

    # Test
    transform_warnings.transform_timing_pick_up_warning(
        report, model, extracted.warnings.timing_pick_up
    )

    # Assert
    warnings = TimingPickUpWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    # Lookup the TimingPattern mentioned in the warnings doc
    timing_pattern = TimingPattern.objects.get(ito_id=warning_json["id"])
    assert warning.timing_pattern == timing_pattern

    # Lookup the stop mentioned in the warnings doc
    timing_pattern_stops = TimingPatternStop.objects.filter(
        timing_pattern=timing_pattern,
        service_pattern_stop__position__in=warning_json["indexes"],
    )

    # Check it matches the stop set in the TimingPickUpWarning
    assert set(warning.timings.values_list("id", flat=True)) == set(
        timing_pattern_stops.values_list("id", flat=True)
    )


def test_transform_timing_drop_off():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/timing-drop_off.json")
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    # get data from report
    with report.file.open("r") as fin:
        data = json.load(fin)["warnings"][0]
        data["warning_type"].replace("-", "_")
        warning_json = data["values"][0]

    extracted = extract.run(report.id)
    model = transform_model.run(extracted)

    # Test
    transform_warnings.transform_timing_drop_off_warning(
        report, model, extracted.warnings.timing_drop_off
    )

    # Assert
    warnings = TimingDropOffWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    # Lookup the TimingPattern mentioned in the warnings doc
    timing_pattern = TimingPattern.objects.get(ito_id=warning_json["id"])
    assert warning.timing_pattern == timing_pattern

    # Lookup the stop mentioned in the warnings doc
    timing_pattern_stops = TimingPatternStop.objects.filter(
        timing_pattern=timing_pattern,
        service_pattern_stop__position__in=warning_json["indexes"],
    )

    # Check it matches the stop set in the TimingLastWarning
    assert set(warning.timings.values_list("id", flat=True)) == set(
        timing_pattern_stops.values_list("id", flat=True)
    )


def test_transform_journey_stop_inappropriate():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/journey-stop_inappropriate.json")
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    # get data from report
    with report.file.open("r") as fin:
        data = json.load(fin)["warnings"][0]
        data["warning_type"].replace("-", "_")
        warning_json = data["values"][0]

    extracted = extract.run(report.id)
    model = transform_model.run(extracted)

    # Test
    transform_warnings.transform_journey_stop_inappropriate_warning(
        report, model, extracted.warnings.journey_stop_inappropriate
    )

    # Assert
    warnings = JourneyStopInappropriateWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    stop = StopPoint.objects.get(ito_id=warning_json["id"])
    assert warning.stop == stop

    vehicle_journeys = VehicleJourney.objects.filter(
        ito_id__in=warning_json["vehicle_journeys"]
    )
    assert set(vj.id for vj in warning.vehicle_journeys.all()) == set(
        vj.id for vj in vehicle_journeys
    )

    assert warning.stop_type == warning_json["stop_type"]


def test_transform_date_range_backwards():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/journey-date_range-backwards.json")
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    # get data from report
    with report.file.open("r") as fin:
        data = json.load(fin)["warnings"][0]
        data["warning_type"].replace("-", "_")
        warning_json = data["values"][0]

    extracted = extract.run(report.id)
    model = transform_model.run(extracted)

    # Test
    transform_warnings.transform_date_range_backwards_warning(
        report, model, extracted.warnings.journey_date_range_backwards
    )

    # Assert
    warnings = JourneyDateRangeBackwardsWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    assert warning.start == parse(warning_json["start"]).date()
    assert warning.end == parse(warning_json["end"]).date()


def test_transform_journey_without_headsign():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/journeys-without-headsign.json")
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    # get data from report
    with report.file.open("r") as fin:
        data = json.load(fin)["warnings"][0]
        data["warning_type"].replace("-", "_")
        data["values"][0]

    extracted = extract.run(report.id)
    model = transform_model.run(extracted)

    # Test
    transform_warnings.transform_journey_without_headsign_warning(
        report, model, extracted.warnings.journeys_without_headsign
    )

    # Assert
    warnings = JourneyWithoutHeadsignWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report
