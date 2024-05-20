from unittest.mock import patch

import pytest

from transit_odp.otc.factories import ServiceModelFactory, LicenceModelFactory
from transit_odp.otc.ep.client import APIResponse
from transit_odp.otc.ep.registry import Registry

pytestmark = pytest.mark.django_db


@pytest.fixture
def get_ep_client_response(get_ep_data):
    return APIResponse(**get_ep_data)


@pytest.fixture
def get_ep_client_blank_response():
    response = {"Results": []}
    return APIResponse(**response)


@pytest.fixture
def get_ep_client_response_from_file(get_ep_data):
    return APIResponse(**get_ep_data)


@pytest.mark.parametrize("get_ep_data", ["ep/duplicate_service.json"], indirect=True)
@patch("transit_odp.otc.ep.registry.EPClient")
def test_ep_registry_duplicate(mock_ep_client, get_ep_client_response_from_file):
    mock_ep_client.return_value.fetch_ep_services.return_value = (
        get_ep_client_response_from_file
    )
    registry = Registry()
    registry.process_services()
    assert len(registry.services) == 2


@patch("transit_odp.otc.ep.registry.EPClient")
def test_fetch_all_records(mock_client, get_ep_client_response):
    # setup
    mock_client.return_value.fetch_ep_services.return_value = get_ep_client_response
    registry = Registry()

    # test
    response = registry.fetch_all_records()

    # assert
    mock_client.return_value.fetch_ep_services.assert_called_once()
    assert response == get_ep_client_response
    assert registry.data == get_ep_client_response.Results


@pytest.mark.parametrize("get_ep_data", ["ep/duplicate_service.json"], indirect=True)
@patch("transit_odp.otc.ep.registry.EPClient")
def test_ep_registry_duplicate(mock_ep_client, get_ep_client_response_from_file):
    mock_ep_client.return_value.fetch_ep_services.return_value = (
        get_ep_client_response_from_file
    )
    registry = Registry()
    registry.process_services()
    assert len(registry.services) == 2


@patch("transit_odp.otc.ep.registry.EPClient")
def test_weca_registry_missing_licence_service(mock_ep_client, get_ep_client_response):
    LicenceModelFactory.create(number="PC2021320", status="Valid")
    LicenceModelFactory.create(number="PF1118394", status="Valid")
    mock_ep_client.return_value.fetch_ep_services.return_value = get_ep_client_response
    registry = Registry()
    registry.process_services()
    missing_licences = registry.get_missing_licences()
    assert len(missing_licences) == 3
