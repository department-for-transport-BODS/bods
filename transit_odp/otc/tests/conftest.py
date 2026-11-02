import json
from pathlib import Path

import pytest
import requests_mock
from django.conf import settings
from tenacity import wait_none

from transit_odp.otc.client import OTCAPIClient
from transit_odp.otc.client.otc_client import APIResponse

HERE = Path(__file__)
TEST_DATA_PATH = HERE.parent / Path("data")
API_DATA_PATH = TEST_DATA_PATH / Path("API")


class TestableOTCAPIClient(OTCAPIClient):
    """
    Testable OTC Client that wont do exponential backoff for broken requests.
    Not having this would significantly slow down the unit tests
    """

    def _make_request(self, *args, **kwargs) -> APIResponse:
        func = super()._make_request
        func.retry.wait = wait_none()
        return func(*args, **kwargs)


def get_data_by_path(path: Path):
    with path.open("r") as file_:
        data = json.load(file_)
    return data


def truncate_data(data):
    data["page"]["totalPages"] = 1
    data["busSearch"] = data["busSearch"][:10]
    return data


def get_weca_data(path="weca/response.json"):
    waca_data = API_DATA_PATH / Path(path)
    return get_data_by_path(waca_data)


@pytest.fixture
def get_ep_data(request):
    path = request.param if hasattr(request, "param") else "ep/response.json"
    ep_file_path = API_DATA_PATH / Path(path)
    return get_data_by_path(ep_file_path)


@pytest.fixture
def otc_data_from_filename_truncated():
    """
    Fixture to provide self-consistent OTC API data
    each status is truncated to 10 entries with the
    corresponding registration numbers being defined
    """
    from_status = API_DATA_PATH / Path("from_status")
    registration_numbers = API_DATA_PATH / Path("registration_numbers")

    with requests_mock.Mocker() as mock:
        for status in from_status.glob("*"):
            page = status / Path("page1.json")
            data = get_data_by_path(page)
            data = truncate_data(data)
            status_qp = status.name
            qp = f"latestVariation=true&page=1&limit=100&regStatus={status_qp}"
            mock.get(f"{settings.OTC_API_URL}?{qp}", json=data)

        for reg_no in registration_numbers.glob("*"):
            for page in reg_no.glob("*"):
                data = get_data_by_path(page)
                page_qp = page.name[4]
                reg_no_qp = reg_no.name.replace("_", "/")
                qp = f"page={page_qp}&limit=100&regNo={reg_no_qp}"
                mock.get(f"{settings.OTC_API_URL}?{qp}", json=data)

        yield mock


@pytest.fixture
def otc_data_from_filename_status():
    """
    Fixture to mock OTC API data when querying per status
    """
    from_status = API_DATA_PATH / Path("from_status")

    with requests_mock.Mocker() as mock:
        for status in from_status.glob("*"):
            for page in status.glob("*"):
                data = get_data_by_path(page)
                page_qp = page.name[4]
                status_qp = status.name
                qp = (
                    f"latestVariation=true"
                    f"&page={page_qp}"
                    "&limit=100"
                    f"&regStatus={status_qp}"
                )
                mock.get(f"{settings.OTC_API_URL}?{qp}", json=data)

        yield mock


def _generate_date_mock(mock, truncate=False):
    from_date = API_DATA_PATH / Path("from_date")
    from_reg_no = API_DATA_PATH / Path("registration_numbers")
    for status in from_date.glob("*"):
        for page in status.glob("*"):
            data = get_data_by_path(page)
            data = truncate_data(data) if truncate else data
            page_qp = page.name[4]
            date_qp = status.name
            qp = (
                f"latestVariation=true"
                f"&page={page_qp}"
                "&limit=100"
                f"&lastModifiedOn={date_qp}"
            )
            mock.get(f"{settings.OTC_API_URL}?{qp}", json=data)

    # add only for truncated data otherwise its too much, probably should be
    # generating these instead of hard coding them but this is actual live data
    for reg_no in from_reg_no.glob("*"):
        page = reg_no / "page1.json"
        data = get_data_by_path(page)
        reg_no_qp = reg_no.name.replace("_", "/")
        qp = f"page=1&limit=100&regNo={reg_no_qp}"
        mock.get(f"{settings.OTC_API_URL}?{qp}", json=data)
    return mock


@pytest.fixture
def otc_data_from_filename_date():
    """
    Fixture to mock OTC API data when querying per day
    """
    # total registrations in the data
    # 2022-11-04 => 137
    # 2022-11-05 => 12
    # 2022-11-06 => 2
    # 2022-11-07 => 147
    # 2022-11-08 => 210

    with requests_mock.Mocker() as mock:
        _generate_date_mock(mock)
        yield mock


@pytest.fixture
def date_data_with_no_content(otc_data_from_filename_date):
    """
    Same as above but just kill middle day and return no content
    """
    # total registrations in the data
    # 2022-11-04 => 137
    # 2022-11-05 => 12
    # 2022-11-06 => 0
    # 2022-11-07 => 147
    # 2022-11-08 => 210
    mock = otc_data_from_filename_date
    qp = "latestVariation=true&page=1&limit=100&lastModifiedOn=2022-11-06"
    mock.get(f"{settings.OTC_API_URL}?{qp}", text="", status_code=204)
    yield mock


@pytest.fixture
def otc_date_data_truncated():
    # total registrations in the data
    # 2022-11-04 => 10
    # 2022-11-05 => 10
    # 2022-11-06 => 2
    # 2022-11-07 => 10
    # 2022-11-08 => 10

    with requests_mock.Mocker() as mock:
        _generate_date_mock(mock, truncate=True)
        yield mock


@pytest.fixture
def otc_date_data_truncated_no_content(otc_date_data_truncated):
    """
    Same as above but just kill middle day and return no content
    """
    # total registrations in the data
    # 2022-11-04 => 10
    # 2022-11-05 => 10
    # 2022-11-06 => 0
    # 2022-11-07 => 10
    # 2022-11-08 => 10
    mock = otc_date_data_truncated
    qp = "latestVariation=true&page=1&limit=100&lastModifiedOn=2022-11-06"
    mock.get(f"{settings.OTC_API_URL}?{qp}", text="", status_code=204)
    yield mock


@pytest.fixture
def weca_get_agliebase_data():
    with requests_mock.Mocker() as mock:
        data = get_weca_data("weca/response.json")
        mock.post(
            f"{settings.WECA_API_URL}?c={settings.WECA_PARAM_C}&t={settings.WECA_PARAM_T}&r={settings.WECA_PARAM_R}&get_report_json=true&json_format=json",
            json=data,
        )
    yield mock
