from unittest.mock import MagicMock, patch

import requests
from django.http.request import QueryDict
from lxml.etree import Element, SubElement, tostring
from requests import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_410_GONE

from transit_odp.api.views.avl import _get_consumer_api_response, _get_gtfs_rt_response


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


@patch("transit_odp.api.views.avl.requests")
def test_get_consumer_api_response_non_200(mrequests):
    """Test function when a non-200 status code returned"""
    url = "http://fakeapi.com/datafeed"
    query_params = QueryDict("originRef=12345")
    mresponse = MagicMock(spec=Response, status_code=HTTP_410_GONE)
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_consumer_api_response(url, query_params)
    mrequests.get.assert_called_once_with(url, params=query_params, timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.avl.requests")
def test_get_consumer_api_response(mrequests):
    url = "http://fakeapi.com/datafeed"
    query_params = QueryDict("operatorRef=12345")
    siri_element = Element("SIRI")
    siri_element.text = "Siri response"
    mresponse = MagicMock(
        spec=Response, status_code=HTTP_200_OK, content=tostring(siri_element)
    )
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_consumer_api_response(url, query_params)
    mrequests.get.assert_called_once_with(url, params=query_params, timeout=60)
    assert actual_content == tostring(siri_element)
    assert actual_status == HTTP_200_OK


@patch("transit_odp.api.views.avl.requests")
def test_get_consumer_api_response_exception(mrequests):
    url = "http://fakeapi.com/datafeed"
    query_params = QueryDict("originRef=12345")
    mrequests.get.side_effect = requests.Timeout
    actual_content, actual_status = _get_consumer_api_response(url, query_params)
    mrequests.get.assert_called_once_with(url, params=query_params, timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.avl.requests")
def test_get_gtfs_rt_response(mrequests):
    url = "http://fakeapi.com/datafeed"
    query_params = {"routeId": "12345"}
    gtfs_rt_content = b"\n\r\n\x032.0\x10\x00\x18\xf4\xb6\x82\xfb\x05"
    mresponse = MagicMock(
        spec=Response, status_code=HTTP_200_OK, content=gtfs_rt_content
    )
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_gtfs_rt_response(url, query_params)
    mrequests.get.assert_called_once_with(url, params=query_params, timeout=60)

    assert actual_content == gtfs_rt_content
    assert actual_status == HTTP_200_OK


@patch("transit_odp.api.views.avl.requests")
def test_get_gtfs_rt_response_exception(mrequests):
    url = "http://fakeapi.com/datafeed"
    query_params = {"routeId": "12345"}
    mrequests.get.side_effect = requests.Timeout

    actual_content, actual_status = _get_gtfs_rt_response(url, query_params)

    mrequests.get.assert_called_once_with(url, params=query_params, timeout=60)
    error_msg = "Unable to process request at this time."
    response_status = HTTP_400_BAD_REQUEST
    expected_content = f"{response_status}: {error_msg}."

    assert actual_content == expected_content
    assert actual_status == HTTP_400_BAD_REQUEST
