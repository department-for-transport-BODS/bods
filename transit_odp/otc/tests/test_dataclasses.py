import json
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
        "registrationNumber": "ABC124",
        "variationNumber": 1,
        "operatorId": 123,
        "contactAddress1": "231 Main St",
        "serviceNumber": "642|231,678",
        "otherServiceNumber": "Park & Ride",
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
        "registrationNumber": "ABC124",
        "variationNumber": 1,
        "operatorId": 123,
        "contactAddress1": "231 Main St",
        "serviceNumber": "642|231,678",
        "otherServiceNumber": "Park & Ride",
    },
]

expected_results = [
    "642",
    "&|678|Park|231|642|Ride",
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
