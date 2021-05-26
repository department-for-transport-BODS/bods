import json
import os
from pathlib import PurePath

import pytest
from dateutil.parser import parse
from django.contrib.gis.geos import LineString

from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.models import (
    FastLinkWarning,
    FastTimingWarning,
    JourneyConflictWarning,
    JourneyDateRangeBackwardsWarning,
    JourneyDuplicateWarning,
    JourneyStopInappropriateWarning,
    JourneyWithoutHeadsignWarning,
    ServiceLink,
    ServiceLinkMissingStopWarning,
    ServicePattern,
    SlowLinkWarning,
    SlowTimingWarning,
    StopIncorrectTypeWarning,
    StopMissingNaptanWarning,
    StopPoint,
    TimingBackwardsWarning,
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


def test_transform_service_link_missing_stops():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/service-link-missing-stops.json")
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
    transform_warnings.transform_service_link_missing_stops(
        report, model, extracted.warnings.service_link_missing_stops
    )

    # Assert
    warnings = ServiceLinkMissingStopWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report
    assert warning.service_link.ito_id == "SL005b3c9d9ce8c688040ba4ee6baae14502b9d623"
    assert warning.service_link.geometry == LineString(
        [
            [0.137484664171875576, 52.1940786889398183],
            [-0.249862338202943901, 52.5745735187174859],
        ],
        srid=4326,
    )

    # Check the m2m associations have been created
    assert set(warning.stops.values_list("ito_id", flat=True)) == {"ST9100ELYY"}

    # Check that the ServicePatterns are available
    service_patterns_in = warning_json["service_patterns"]
    sl = ServiceLink.objects.get(id=warning.service_link_id)
    service_patterns = sl.service_patterns.all()
    assert set(sp.ito_id for sp in service_patterns) == set(service_patterns_in)


@pytest.mark.parametrize(
    "filename, warning_class",
    [
        ["data/timing-fast-link.json", FastLinkWarning],
        ["data/timing-fast.json", FastTimingWarning],
        ["data/timing-slow-link.json", SlowLinkWarning],
        ["data/timing-slow.json", SlowTimingWarning],
    ],
)
def test_transform_timing_speed_warnings(filename, warning_class):
    # Setup
    testfile = os.path.join(FILE_DIR, filename)
    report = DataQualityReportFactory(
        file__from_path=testfile, revision__upload_file__from_path=TXCFILE
    )

    # get data from report
    with report.file.open("r") as fin:
        data = json.load(fin)["warnings"][0]
        warning_type = data["warning_type"].replace("-", "_")
        warning_json = data["values"][0]

    extracted = extract.run(report.id)
    model = transform_model.run(extracted)

    # Test
    transform_warnings.transform_timing_warning(
        report, model, getattr(extracted.warnings, warning_type), warning_type
    )

    # Assert
    warnings = warning_class.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    timing_pattern = TimingPattern.objects.get(ito_id=warning_json["id"])
    assert warning.timing_pattern == timing_pattern

    timing_pattern_stops = TimingPatternStop.objects.filter(
        timing_pattern=timing_pattern,
        service_pattern_stop__position__in=warning_json["indexes"],
    )

    assert set(warning.timings.values_list("id", flat=True)) == set(
        timing_pattern_stops.values_list("id", flat=True)
    )

    if warning_type == "timing_fast_link" or warning_type == "timing_slow_link":
        sl_id = warning_json["service_link"]
        service_link = ServiceLink.objects.get(ito_id=sl_id)

        assert warning.service_links.values_list("id", flat=True)[0] == service_link.id

    else:
        service_links = ServiceLink.objects.filter(ito_id__in=warning_json["entities"])

        assert set(warning.service_links.values_list("id", flat=True)) == set(
            service_links.values_list("id", flat=True)
        )


def test_transform_timing_backwards():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/timing-backwards.json")
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
    transform_warnings.transform_timing_backwards_warning(
        report, model, extracted.warnings.timing_backwards
    )

    # Assert
    warnings = TimingBackwardsWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    # Lookup the TimingPattern mentioned in the warnings doc
    timing_pattern = TimingPattern.objects.get(ito_id=warning_json["id"])
    assert warning.timing_pattern == timing_pattern

    # Lookup the stop mentioned in the warnings doc
    service_link_index = warning_json["indexes"][0]
    from_stop = TimingPatternStop.objects.get(
        timing_pattern=timing_pattern,
        service_pattern_stop__position=service_link_index,
    )
    to_stop = TimingPatternStop.objects.get(
        timing_pattern=timing_pattern,
        service_pattern_stop__position=service_link_index + 1,
    )

    assert warning.from_stop == from_stop
    assert warning.to_stop == to_stop


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


def test_transform_stop_missing_naptan():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/stop-missing-naptan.json")
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
    transform_warnings.transform_stop_missing_naptan_warning(
        report, model, extracted.warnings.stop_missing_naptan
    )

    # Assert
    warnings = StopMissingNaptanWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    stop = StopPoint.objects.get(ito_id=warning_json["id"])
    assert warning.stop == stop

    service_patterns = ServicePattern.objects.filter(
        ito_id__in=warning_json["service_patterns"]
    )
    assert set(sp.id for sp in warning.service_patterns.all()) == set(
        sp.id for sp in service_patterns
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


def test_transform_journey_duplicate():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/journey-duplicate.json")
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
    transform_warnings.transform_journey_duplicate_warning(
        report, model, extracted.warnings.journey_duplicate
    )

    # Assert
    warnings = JourneyDuplicateWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    assert warning.duplicate.ito_id == warning_json["duplicate"]


def test_transform_journey_conflict():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/journey-conflict.json")
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
    transform_warnings.transform_journey_conflict_warning(
        report, model, extracted.warnings.journey_conflict
    )

    # Assert
    warnings = JourneyConflictWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    assert warning.conflict.ito_id == warning_json["conflict"]

    stops = StopPoint.objects.filter(ito_id__in=warning_json["stops"])
    assert set(s.ito_id for s in stops) == set(warning_json["stops"])


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


def test_transform_stop_incorrect_type():
    # Setup
    testfile = os.path.join(FILE_DIR, "data/stop-incorrect-type.json")
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
    transform_warnings.transform_stop_incorrect_type_warning(
        report, model, extracted.warnings.stop_incorrect_type
    )

    # Assert
    warnings = StopIncorrectTypeWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == report

    stop = StopPoint.objects.get(ito_id=warning_json["id"])
    assert warning.stop == stop

    assert warning.stop_type == warning_json["stop_type"]

    service_patterns = ServicePattern.objects.filter(
        ito_id__in=warning_json["service_patterns"]
    )
    assert set(sp.id for sp in warning.service_patterns.all()) == set(
        sp.id for sp in service_patterns
    )
