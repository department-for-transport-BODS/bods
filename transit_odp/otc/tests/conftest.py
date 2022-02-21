from pathlib import Path

import pytest
import requests_mock

from transit_odp.otc.constants import CSV_FILE_TEMPLATE, OTC_CSV_URL, TrafficAreas

HERE = Path(__file__)
CSV_PATH = HERE.parent / Path("data")
CSV_DATA = [
    # The values were calculated using pandas, Service codes that are either
    # empty or "N/A" are dropped by the code
    # Columns are:
    # traffic area, total registrations, total operators, total services, total licences
    ("B", 3516, 133, 2527, 133),
    ("C", 3546, 147, 2441, 147),
    ("D", 6683, 70, 1235, 70),
    ("F", 2824, 140, 1853, 140),
    ("G", 1614, 82, 1114, 82),
    ("H", 8508, 123, 1997, 123),
    ("K", 1562, 72, 1003, 72),
    ("M", 3039, 155, 2098, 155),
]


def read_csv(otc_traffic_area):
    filepath = CSV_PATH / Path(CSV_FILE_TEMPLATE.format(otc_traffic_area))
    with open(filepath, "r") as test_csv:
        return test_csv.read()


@pytest.fixture
def otc_urls():
    with requests_mock.Mocker() as m:
        for cta in TrafficAreas.values:
            m.get(f"{OTC_CSV_URL}/{CSV_FILE_TEMPLATE.format(cta)}", text=read_csv(cta))
        yield m


@pytest.fixture
def bad_otc_urls():
    with requests_mock.Mocker() as m:
        for cta in TrafficAreas.values:
            m.get(f"{OTC_CSV_URL}/{CSV_FILE_TEMPLATE.format(cta)}", status_code=403)
        yield m
