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


@pytest.fixture
def otc_data_from_filename_truncated():
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
