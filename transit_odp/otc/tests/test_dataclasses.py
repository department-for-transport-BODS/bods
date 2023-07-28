import json
from pathlib import Path

import pytest
from transit_odp.otc.dataclasses import Registration

json_data = {
    "timeStamp": "11/11/2022 17:42:47",
    "busSearch": [
        {
            "id": "49973",
            "operatorId": "97592",
            "operatorName": "THOMAS ANELAY",
            "registrationNumber": "PB0000006/2",
            "registrationStatus": "Registered",
            "routeNumber": "2",
            "licenceNumber": "PB0000006",
            "licenceId": "155079",
            "licenceStatus": "Surrendered",
            "licenceType": "Standard International",
            "licenceGoodsOrPsv": "Public Service Vehicle",
            "psvDiscsToBePrintedNumber": "0",
            "serviceNumber": " 642 ",
            "otherServiceNumber": None,
            "variationNumber": "0",
            "startPoint": "Redbourne",
            "finishPoint": "Scunthorpe",
            "via": None,
            "subsidised": "No",
            "subsidyDetail": None,
            "busServiceTypeId": None,
            "busServiceTypeDescription": None,
            "otherDetails": None,
            "routeDescription": None,
            "isShortNotice": "No",
            "localAuthorities": None,
            "tradingName": "BLACK & WHITE COACHES",
            "trafficAreaId": "B",
            "taoCoveredByArea": "North East of England",
            "publicationText": None,
            "contactDetailsId": "467539",
            "contactAddress1": "22B HEBDEN ROAD",
            "contactAddress2": None,
            "contactAddress3": None,
            "contactAddress4": "SCUNTHORPE",
            "contactPostCode": "DN15 8DT",
            "discsInPossession": None,
            "authDiscs": "8",
            "lastModifiedOn": "02/09/2002 17:52:01",
            "registrationCode": "2",
            "applicationType": None,
            "expiryDate": "31/10/2021",
            "grantedDate": "12/11/1991",
            "effectiveDate": "02/09/2002",
            "receivedDate": None,
            "endDate": None,
        },
    ],
    "page": {"current": 1, "totalCount": 21598, "totalPages": 5, "perPage": 100},
}


def create_registration_objects(json_data):
    registrations = []
    for item in json_data["busSearch"]:
        reg = Registration(
            service_number=item["serviceNumber"],
            other_service_number=item["otherServiceNumber"],
            variation_number=item["variationNumber"],
            # Add other fields as needed...
        )
        registrations.append(reg)
    return registrations


def test_combine_service_numbers():
    # Create Registration objects from JSON data
    registrations = create_registration_objects(json_data)

    # Test combine_service_numbers on each Registration object
    for reg in registrations:
        combined_numbers = reg.combine_service_numbers()
        print(combined_numbers)  # Replace with assertions based on your requirements
