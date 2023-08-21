import pytest
from transit_odp.otc.dataclasses import (
    Registration,
)

test_data_sets = [
    {
        "registrationNumber": "ABC123",
        "variationNumber": 1,
        "operatorId": 123,
        "contactAddress1": "123 Main St",
        "serviceNumber": "642",
        "otherServiceNumber": None,
    },
    {
        "registrationNumber": "ABC124",
        "variationNumber": 1,
        "operatorId": 123,
        "contactAddress1": "231 Main St",
        "serviceNumber": "642|231,678",
        "otherServiceNumber": "Park & Ride",
    },
    {
        "registrationNumber": "ABC121",
        "variationNumber": 1,
        "operatorId": 123,
        "contactAddress1": "231 Main St",
        "serviceNumber": "642|231,678",
        "otherServiceNumber": "231|435-456 21",
    },
    {
        "registrationNumber": "ABC125",
        "variationNumber": 1,
        "operatorId": 123,
        "contactAddress1": "231 Main St",
        "serviceNumber": "642|231,678",
        "otherServiceNumber": "",
    },
    {
        "registrationNumber": "ABC127",
        "variationNumber": 1,
        "operatorId": 123,
        "contactAddress1": "231 Main St",
        "serviceNumber": "Cotgrave Connection",
        "otherServiceNumber": "878N 23H 909|POP",
    },
]

expected_results = [
    "642",
    "642|231|678|Park|&|Ride",
    "642|231|678|435|456|21",
    "642|231,678",
    "Cotgrave|Connection|878N|23H|909|POP",
]


@pytest.mark.parametrize(
    "test_data, expected_result", zip(test_data_sets, expected_results)
)
def test_combine_service_numbers(test_data, expected_result):
    service_number = test_data["serviceNumber"]
    other_service_number = test_data["otherServiceNumber"]

    registration = Registration(**test_data)

    combined_result = registration.combine_service_numbers(
        v=service_number, values=registration.__dict__
    )

    assert combined_result == expected_result
