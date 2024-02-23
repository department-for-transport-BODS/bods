import pytest
from unittest.mock import patch
from requests.exceptions import HTTPError

from transit_odp.otc.weca.client import WecaClient


def test_weca_api_response_returned(weca_get_agliebase_data):
    with weca_get_agliebase_data:
        client = WecaClient()
        response = client.fetch_weca_services()
        assert len(response.data) == 5
        assert len(response.fields) == 12


@patch("django.conf.settings.WECA_PARAM_C", "dummay_weca_param_c")
def test_weca_api_response_error():
    with pytest.raises(HTTPError) as e:
        client = WecaClient()
        response = client.fetch_weca_services()
