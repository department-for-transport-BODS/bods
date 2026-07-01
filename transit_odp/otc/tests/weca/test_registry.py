from unittest.mock import patch

import pytest

from transit_odp.otc.factories import ServiceModelFactory, LicenceModelFactory
from transit_odp.otc.tests.conftest import get_weca_data
from transit_odp.otc.weca.client import WECAResponse
from transit_odp.otc.weca.registry import Registry

pytestmark = pytest.mark.django_db

CLIENT = "transit_odp.otc.weca.client.WecaClient.fetch_weca_services"


def get_weca_client_response():
    return WECAResponse(**get_weca_data())


def get_weca_client_response_from_file(filename):
    return WECAResponse(**get_weca_data(filename))


def get_weca_client_blank_response():
    response = {"fields": [], "data": []}
    return WECAResponse(**response)


@patch(CLIENT)
def test_weca_registry(mock_weca_fetch):
    mock_weca_fetch.return_value = get_weca_client_response()

    registry = Registry()
    response = registry.fetch_all_records()

    assert type(response) == WECAResponse
    assert len(registry.data) == 5
    assert len(registry.fields) == 12


@patch(CLIENT)
def test_weca_registry_blank_response(mock_weca_fetch):
    mock_weca_fetch.return_value = get_weca_client_blank_response()

    registry = Registry()
    response = registry.fetch_all_records()

    assert type(response) == WECAResponse
    assert len(registry.data) == 0
    assert len(registry.fields) == 0


@patch(CLIENT)
def test_weca_registry_duplicate(mock_weca_fetch):
    mock_weca_fetch.return_value = get_weca_client_response_from_file(
        "weca/duplicate_service.json"
    )
    registry = Registry()
    registry.process_services()
    assert len(registry.services) == 3


@patch(CLIENT)
def test_weca_same_line_name(mock_weca_fetch):
    mock_weca_fetch.return_value = get_weca_client_response_from_file(
        "weca/weca_same_line_name.json"
    )
    registry = Registry()
    registry.process_services()
    assert len(registry.services) == 2
    service = registry.services.loc[
        registry.services["registration_number"] == "PH0007180/01010012"
    ]
    assert (service["service_number"] == "734|716|779|700").bool() == True


@patch(CLIENT)
def test_weca_registry_otc_service(mock_weca_fetch):
    ServiceModelFactory.create(registration_number="PH2023619/19")
    mock_weca_fetch.return_value = get_weca_client_response_from_file(
        "weca/otc_service.json"
    )
    registry = Registry()
    registry.process_services()
    assert len(registry.services) == 3


@patch(CLIENT)
def test_weca_registry_missing_licence_service(mock_weca_fetch):
    """Test for the services when some licence is missing,
    and few are present in the database, So missing licences
    will return only licences which are missing in the database

    Args:
        mock_weca_fetch
    """
    LicenceModelFactory.create(number="PH0006633", status="Valid")
    LicenceModelFactory.create(number="PH0006347", status="Valid")
    mock_weca_fetch.return_value = get_weca_client_response_from_file(
        "weca/otc_service.json"
    )
    registry = Registry()
    registry.process_services()
    missing_licences = registry.get_missing_licences()
    assert len(missing_licences) == 2
