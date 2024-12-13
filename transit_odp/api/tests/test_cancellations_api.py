from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests
from lxml.etree import Element, SubElement, tostring
from requests import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from transit_odp.api.views.cancellations import _get_consumer_api_response
from transit_odp.api.utils.response_utils import create_xml_error_response


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


@patch("transit_odp.api.views.cancellations.requests")
def test_get_cancellations_api_view_non_200(mrequests):
    """Test function when a non-200 status code returned"""
    url = "http://testcancellationsapi.com/siri-sx/cancellations"
    mresponse = MagicMock(spec=Response, status_code=HTTP_400_BAD_REQUEST)
    mresponse.elapsed = timedelta(seconds=1)
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_consumer_api_response(url, {})
    mrequests.get.assert_called_once_with(url, params={}, timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.cancellations.requests")
def test_get_cancellations_api_response(mrequests):
    url = "http://testapi.com/siri-sx/cancellations"
    cancellations_content = "hello"
    mresponse = MagicMock(
        spec=Response, status_code=HTTP_200_OK, content=cancellations_content
    )
    mresponse.elapsed = timedelta(seconds=1)
    mrequests.get.return_value = mresponse
    actual_content, actual_status = _get_consumer_api_response(url, {})
    mrequests.get.assert_called_once_with(url, params={}, timeout=60)

    assert actual_content == cancellations_content
    assert actual_status == HTTP_200_OK


@patch("transit_odp.api.views.cancellations.requests")
def test_get_cancellations_api_invalid_query_params(mrequests):
    url = "http://testapi.com/siri-sx/cancellations"
    query_params = {"unknownParam": "12345"}
    mrequests.get.side_effect = requests.Timeout
    actual_content, actual_status = _get_consumer_api_response(url, query_params)
    mrequests.get.assert_not_called()
    assert actual_content == create_xml_error_response(
        "Parameter unknownParam is not valid.", HTTP_400_BAD_REQUEST
    )
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.cancellations.requests")
def test_get_cancellations_api_response_exception(mrequests):
    url = "http://testapi.com/siri-sx/cancellations"
    mrequests.get.side_effect = requests.Timeout
    actual_content, actual_status = _get_consumer_api_response(url, {})
    mrequests.get.assert_called_once_with(url, params={}, timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST
