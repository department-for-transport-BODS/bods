from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests
from lxml.etree import Element, SubElement, tostring
from requests import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from transit_odp.api.views.disruptions import (
    _get_consumer_api_response,
    _get_gtfs_rt_response,
)


def get_error_element():
    """Get a standard error response element."""
    error_element = Element("response")

    error_msg = "Unable to process request at this time."
    error_code = HTTP_400_BAD_REQUEST
    description = SubElement(error_element, "error_description")
    code = SubElement(error_element, "error_code")
    description.text = error_msg
    code.text = f"{error_code}"

    return error_element


@patch("transit_odp.api.views.disruptions.requests")
def test_get_disruptions_api_view_non_200(mrequests):
    """Test function when a non-200 status code returned"""
    url = "http://testdisruptionsapi.com/siri-sx"
    headers = {"test": "test"}
    mresponse = MagicMock(spec=Response, status_code=HTTP_400_BAD_REQUEST)
    mresponse.elapsed = timedelta(seconds=1)
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_consumer_api_response(url, headers)
    mrequests.get.assert_called_once_with(url, headers={"test": "test"}, timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.disruptions.requests")
def test_get_disruptions_api_response(mrequests):
    url = "http://testapi.com/siri-sx"
    headers = {"test": "test"}
    disruptions_content = b"\n\r\n\x032.0\x10\x00\x18\xf4\xb6\x82\xfb\x05"
    mresponse = MagicMock(
        spec=Response, status_code=HTTP_200_OK, content=disruptions_content
    )
    mresponse.elapsed = timedelta(seconds=1)
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_consumer_api_response(url, headers)
    mrequests.get.assert_called_once_with(url, headers={"test": "test"}, timeout=60)

    assert actual_content == disruptions_content
    assert actual_status == HTTP_200_OK


@patch("transit_odp.api.views.disruptions.requests")
def test_get_disruptions_api_response_exception(mrequests):
    url = "http://testapi.com/siri-sx"
    headers = {"test": "test"}
    mrequests.get.side_effect = requests.Timeout
    actual_content, actual_status = _get_consumer_api_response(url, headers)
    mrequests.get.assert_called_once_with(url, headers={"test": "test"}, timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.disruptions.requests")
def test_get_service_alerts_api_response_exception(mrequests):
    url = "http://testapi.com/gtfs-rt/service-alerts"
    mrequests.get.side_effect = requests.Timeout
    actual_content, actual_status = _get_gtfs_rt_response(url)
    mrequests.get.assert_called_once_with(url, timeout=60, params="api_key")
    assert actual_content == "400: Unable to process request at this time.."
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.disruptions.requests")
def test_get_service_alerts_api_response(mrequests):
    url = "http://testapi.com/gtfs-rt/service-alerts"
    mresponse = MagicMock(
        spec=Response, status_code=HTTP_200_OK, content="test_content"
    )
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_gtfs_rt_response(url)
    mrequests.get.assert_called_once_with(url, timeout=60, params="api_key")
    assert actual_content == mresponse.content
    assert actual_status == HTTP_200_OK
