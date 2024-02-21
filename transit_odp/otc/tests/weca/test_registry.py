import pytest
from unittest.mock import patch
from requests.exceptions import HTTPError
from transit_odp.otc.tests.conftest import get_weca_data
from transit_odp.otc.weca.client import APIResponse
from transit_odp.otc.weca.registry import Registry

CLIENT = "transit_odp.otc.weca.client.WecaClient.fetch_weca_services"

def get_weca_client_response():
    return APIResponse(**get_weca_data())

@patch(CLIENT)
def test_weca_registry(mock_weca_fetch):
    mock_weca_fetch.return_value = get_weca_client_response()
    
    registry = Registry()
    response = registry.fetch_all_records()

    assert(type(response) == APIResponse)
    assert(len(registry.services) == 5)
    assert(len(registry.fields) == 12)