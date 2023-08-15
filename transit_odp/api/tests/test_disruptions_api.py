from datetime import timedelta
from unittest.mock import MagicMock, patch
from rest_framework.test import APITestCase

import requests
from lxml.etree import Element, SubElement, tostring
from requests import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_406_NOT_ACCEPTABLE
from transit_odp.api.views.disruptions import DisruptionsApiView


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
@api_view(('GET',))
@renderer_classes(TemplateHTMLRenderer)
def test_get_disruptions_api_view_non_200(mrequests):
    """Test function when a non-200 status code returned"""
    url = "http://testdisruptionsapi.com/siri-sx"
    mresponse = MagicMock(spec=Response, status_code=HTTP_400_BAD_REQUEST)
    mresponse.elapsed = timedelta(seconds=1)
    mrequests.get.return_value = mresponse
    actual_content, actual_status = DisruptionsApiView().get()
    mrequests.get.assert_called_once_with(timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.disruptions.requests")
@api_view(('GET',))
@renderer_classes(TemplateHTMLRenderer)
def test_get_disruptions_api_response_exception(mrequests):
    url = "http://testapi.com/siri-sx"
    mrequests.get.side_effect = requests.Timeout
    actual_content, actual_status = DisruptionsApiView().get()
    mrequests.get.assert_called_once_with(timeout=60)
    assert actual_content == tostring(get_error_element())
    assert actual_status == HTTP_400_BAD_REQUEST


@patch("transit_odp.api.views.disruptions.requests")
@api_view(('GET',))
@renderer_classes(TemplateHTMLRenderer)
def test_get_disruptions_api_response(mrequests):
    url = "http://testapi.com/siri-sx"
    disruptions_content = b"\n\r\n\x032.0\x10\x00\x18\xf4\xb6\x82\xfb\x05"
    mresponse = MagicMock(
        spec=Response, status_code=HTTP_200_OK, content=disruptions_content
    )
    mrequests.get.return_value = mresponse
    actual_content, actual_status = DisruptionsApiView().get()
    mrequests.get.assert_called_once_with(timeout=60)

    assert actual_content == disruptions_content
    assert actual_status == HTTP_200_OK
