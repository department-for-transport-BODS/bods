import json
import os
from pathlib import PurePath

import pytest
from dateutil.parser import parse

from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.models import (
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
