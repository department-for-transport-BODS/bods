from unittest.mock import Mock, call, patch

import pytest

from transit_odp.organisation.csv.service_codes import ServiceCodesCSV
from transit_odp.organisation.factories import DatasetFactory
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.constants import FLEXIBLE_REG, SCHOOL_OR_WORKS
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory

pytestmark = pytest.mark.django_db


def test_queryset():
    licence_number1 = "PD000001"
    otc_lic1 = LicenceModelFactory(number=licence_number1)
    service_code1 = f"{licence_number1}:001"
    ServiceModelFactory(
        licence=otc_lic1,
        registration_number=service_code1,
        service_type_description=FLEXIBLE_REG,
    )
    ServiceModelFactory(
        licence=otc_lic1,
        registration_number=service_code1,
        service_type_description=SCHOOL_OR_WORKS,
    )

    licence_number2 = "PA000002"
    otc_lic2 = LicenceModelFactory(number=licence_number2)
    service_code2 = f"{licence_number2}:001"
    service_code3 = f"{licence_number2}:002"
    ServiceModelFactory(licence=otc_lic2, registration_number=service_code2)
    ServiceModelFactory(licence=otc_lic2, registration_number=service_code3)

    licence_number3 = "PB000003"
    otc_lic3 = LicenceModelFactory(number=licence_number3)
    service_code4 = f"{licence_number3}:001"
    service_code5 = f"{licence_number3}:002"
    ServiceModelFactory(licence=otc_lic3, registration_number=service_code4)
    ServiceModelFactory(licence=otc_lic3, registration_number=service_code5)

    org1 = OrganisationFactory()
    BODSLicenceFactory(organisation=org1, number=licence_number1)
    BODSLicenceFactory(organisation=org1, number=licence_number2)
    org2 = OrganisationFactory()
    BODSLicenceFactory(organisation=org2, number=licence_number3)

    expected_pairs_org1 = [
        (licence_number1, service_code1),
        (licence_number2, service_code2),
        (licence_number2, service_code3),
    ]

    service_codes_csv = ServiceCodesCSV(org1.id)
    queryset = service_codes_csv.get_queryset()
    assert queryset.count() == len(expected_pairs_org1)

    queryset_pairs = [
        (service.licence.number, service.service_code) for service in queryset
    ]
    assert sorted(queryset_pairs) == sorted(expected_pairs_org1)


def test_missing_service_code():
    licence_number = "PD000001"
    otc_service_code = f"{licence_number}:001"
    otc_service_number = "Line1"
    bods_service_code = f"{licence_number}:001X"

    org1 = OrganisationFactory()
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision, service_code=bods_service_code
    )

    otc_lic1 = LicenceModelFactory(number=licence_number)
    ServiceModelFactory(
        licence=otc_lic1,
        registration_number=otc_service_code,
        service_number=otc_service_number,
    )

    service_codes_csv = ServiceCodesCSV(org1.id)

    queryset = service_codes_csv.get_queryset()
    assert queryset.count() == 1
    row = service_codes_csv.get_row(queryset.first())
    assert row[0] == ServiceCodesCSV.MISSING_DATA
    assert row[1] == licence_number
    assert row[2] == otc_service_code
    assert row[3] == otc_service_number
    assert row[4] == ""


def test_registered_service_code():
    licence_number = "PD000001"
    service_code = f"{licence_number}:001"
    service_number = "Line1"

    org1 = OrganisationFactory()
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(revision=dataset1.live_revision, service_code=service_code)
    dataset2 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(revision=dataset2.live_revision, service_code=service_code)

    otc_lic1 = LicenceModelFactory(number=licence_number)
    ServiceModelFactory(
        licence=otc_lic1,
        registration_number=service_code,
        service_number=service_number,
    )

    service_codes_csv = ServiceCodesCSV(org1.id)

    queryset = service_codes_csv.get_queryset()
    assert queryset.count() == 1
    row = service_codes_csv.get_row(queryset.first())
    assert row[0] == ServiceCodesCSV.REGISTERED
    assert row[1] == licence_number
    assert row[2] == service_code
    assert row[3] == service_number
    assert row[4] in [f"{dataset1.id};{dataset2.id}", f"{dataset2.id};{dataset1.id}"]


@patch("transit_odp.organisation.csv.service_codes.csv.writer")
def test_csv_output(mock_csv_writer):
    licence_number = "PD000001"
    num_otc_services = 3
    service_codes = [f"{licence_number}:{n:03}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org1 = OrganisationFactory()
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision, service_code=service_codes[0]
    )

    otc_lic = LicenceModelFactory(number=licence_number)
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[1],
        service_number=service_numbers[1],
    )
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[0],
        service_number=service_numbers[0],
    )
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[2],
        service_number=service_numbers[2],
    )

    mock_writer = Mock()
    mock_csv_writer.return_value = mock_writer

    service_codes_csv = ServiceCodesCSV(org1.id)
    _ = service_codes_csv.to_csv()

    assert mock_writer.writerow.call_count == 1 + num_otc_services
    call_args_list = mock_writer.writerow.call_args_list
    assert call_args_list[0] == call(
        ("Service Status", "Licence Number", "Service Code", "Line", "Dataset ID")
    )
    expected_missing_rows = [
        call(
            (
                ServiceCodesCSV.MISSING_DATA,
                licence_number,
                service_codes[1],
                service_numbers[1],
                "",
            )
        ),
        call(
            (
                ServiceCodesCSV.MISSING_DATA,
                licence_number,
                service_codes[2],
                service_numbers[2],
                "",
            )
        ),
    ]
    assert call_args_list[1] in expected_missing_rows
    assert call_args_list[2] in expected_missing_rows
    assert call_args_list[3] == call(
        (
            ServiceCodesCSV.REGISTERED,
            licence_number,
            service_codes[0],
            service_numbers[0],
            str(dataset1.id),
        )
    )
