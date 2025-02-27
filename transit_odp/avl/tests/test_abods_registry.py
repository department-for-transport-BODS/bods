import json
from unittest.mock import Mock, patch

from freezegun import freeze_time
from requests import HTTPError

from transit_odp.avl.require_attention.abods.registery import (
    AbodsClient,
    AbodsRegistery,
    APIResponse,
)

MODULE_PATH = "transit_odp.avl.require_attention.abods.registery"
CLIENT = f"{MODULE_PATH}.AbodsClient.fetch_line_details"
REQUEST = f"{MODULE_PATH}.requests.post"
VALID_RESPONSE = {
    "data": {
        "avlLineLevelStatus": [
            {
                "lineName": 43,
                "lastRecordedAtTime": "2025-02-04T16:40:40.000Z",
                "operatorNoc": "SDCU",
            },
            {
                "lineName": 42,
                "lastRecordedAtTime": "2025-02-07T16:40:40.000Z",
                "operatorNoc": "SDCU",
            },
            {
                "lineName": 41,
                "lastRecordedAtTime": "2025-02-08T16:40:40.000Z",
                "operatorNoc": "SDCU",
            },
            {
                "lineName": 41,
                "lastRecordedAtTime": "2024-02-09T16:40:40.000Z",
                "operatorNoc": "SDCU",
            },
        ]
    }
}

VALIDATION_ERROR_RESPONSE = {
    "data": {
        "avlLineLevelStatus": [
            {
                "lineName": 43,
                "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                "operatorNoc": 2,
            }
        ]
    }
}


def mock_requests_factory(response_stub: str, status_code: int = 200):
    return Mock(
        **{
            "json.return_value": response_stub,
            "text.return_value": response_stub,
            "status_code": status_code,
            "ok": status_code == 200,
        }
    )


def mocked_requests_post_valid_response(*args, **kwargs):
    return mock_requests_factory(VALID_RESPONSE)


def mocked_requests_post_validation_error(*args, **kwargs):
    return mock_requests_factory(VALIDATION_ERROR_RESPONSE)


def mocked_requests_no_content(*args, **kwargs):
    return mock_requests_factory({}, 204)


def get_abods_client_response():
    response = {
        "data": {
            "avlLineLevelStatus": [
                {
                    "lineName": 43,
                    "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                    "operatorNoc": "SDCU",
                },
                {
                    "lineName": 42,
                    "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                    "operatorNoc": "SDCU",
                },
                {
                    "lineName": 41,
                    "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                    "operatorNoc": "SDCU",
                },
                {
                    "lineName": 41,
                    "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                    "operatorNoc": "SDCU",
                },
            ]
        }
    }
    return APIResponse(**response)


def get_abods_client_blank_response():
    response = {"data": {"avlLineLevelStatus": []}}
    return APIResponse(**response)


@patch(CLIENT)
@freeze_time("2024-11-30")
def test_registry_with_success_api_response(mock_client):
    mock_client.return_value = get_abods_client_response()
    registry = AbodsRegistery()
    lines_list = registry.records()
    assert len(lines_list) == 3


@patch(CLIENT)
def test_registry_with_blank_api_response(mock_client):
    mock_client.return_value = get_abods_client_blank_response()
    registry = AbodsRegistery()
    lines_list = registry.records()
    assert len(lines_list) == 0


# ABODS client
@patch("django.conf.settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL", "http://dummy_url.com")
@patch("django.conf.settings.ABODS_AVL_AUTH_TOKEN", "dummy_token")
@patch(REQUEST, side_effect=mocked_requests_post_valid_response)
def test_expected_number_of_lines_returned(mock_request):
    client = AbodsClient()
    line_records = client.fetch_line_details()
    assert len(line_records.data.avlLineLevelStatus) == 4


@patch("django.conf.settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL", "http://dummy_url.com")
@patch("django.conf.settings.ABODS_AVL_AUTH_TOKEN", "dummy_token")
@patch(REQUEST, side_effect=mocked_requests_post_validation_error)
def test_validation_error_exception_returned(mock_request):
    client = AbodsClient()
    line_records = client.fetch_line_details()
    assert len(line_records.data.avlLineLevelStatus) == 0


@patch("django.conf.settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL", "http://dummy_url.com")
@patch("django.conf.settings.ABODS_AVL_AUTH_TOKEN", "dummy_token")
@patch(REQUEST, side_effect=mocked_requests_no_content)
def test_response_no_content(mock_request):
    client = AbodsClient()
    line_records = client.fetch_line_details()
    assert len(line_records.data.avlLineLevelStatus) == 0


@patch("django.conf.settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL", "http://dummy_url.com")
@patch("django.conf.settings.ABODS_AVL_AUTH_TOKEN", "dummy_token")
@patch(REQUEST, side_effect=TimeoutError("Max limit reached"))
def test_request_timeout_error(mock_request):
    client = AbodsClient()
    line_records = client.fetch_line_details()
    assert len(line_records.data.avlLineLevelStatus) == 0


@patch("django.conf.settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL", "http://dummy_url.com")
@patch("django.conf.settings.ABODS_AVL_AUTH_TOKEN", "dummy_token")
@patch(REQUEST, side_effect=HTTPError("HTTP ERROR"))
def test_request_http_error(mock_request):
    client = AbodsClient()
    line_records = client.fetch_line_details()
    assert len(line_records.data.avlLineLevelStatus) == 0


@patch("django.conf.settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL", "http://dummy_url.com")
@patch("django.conf.settings.ABODS_AVL_AUTH_TOKEN", "dummy_token")
@patch(REQUEST, side_effect=Exception("Unexpected exception"))
def test_request_unexpected_exception_error(mock_request):
    client = AbodsClient()
    line_records = client.fetch_line_details()
    assert len(line_records.data.avlLineLevelStatus) == 0
