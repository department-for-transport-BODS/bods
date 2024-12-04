import json
import os
from pathlib import PurePath

import pytest
from dateutil.parser import parse

from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.models import (
    JourneyWithoutHeadsignWarning,
    ServiceLink,
    ServicePattern,
    StopPoint,
    TimingPattern,
    TimingPatternStop,
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
