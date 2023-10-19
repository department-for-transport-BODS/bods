from typing import Dict
import faker

import pytest
from django.db.models.expressions import datetime
from freezegun import freeze_time

from transit_odp.browse.views.local_authority import LTACSV
from transit_odp.organisation.factories import DatasetFactory
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    SeasonalServiceFactory,
    ServiceCodeExemptionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.constants import FLEXIBLE_REG, SCHOOL_OR_WORKS
from transit_odp.otc.factories import (
    LicenceModelFactory,
    LocalAuthorityFactory,
    ServiceModelFactory,
)
from transit_odp.browse.lta_column_headers import header_accessor_data

pytestmark = pytest.mark.django_db
FAKER = faker.Faker()
csv_columns = [header for header, _ in header_accessor_data]
CSV_NUMBER_COLUMNS = len(csv_columns)
national_operator_code = "".join(FAKER.random_letters(length=4)).upper()


def get_csv_output(csv_string: str) -> Dict[str, list]:
    result_list = csv_string.replace("\r\n", ",").split(",")[:-1]
    result = {}
    len_result_list = len(result_list)
    start = 0
    i = 0
    result.update({"header": result_list[start:CSV_NUMBER_COLUMNS]})
    start += CSV_NUMBER_COLUMNS
    for end in range(2 * CSV_NUMBER_COLUMNS, len_result_list + 1, CSV_NUMBER_COLUMNS):
        result.update({f"row{i}": result_list[start:end]})
        start = end
        i += 1
    return result


def test_lta_queryset():
    services_list_1 = []
    services_list_2 = []
    licence_number1 = "PD000001"
    otc_lic1 = LicenceModelFactory(number=licence_number1)
    registration_number1 = f"{licence_number1}/1"
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=registration_number1,
            service_type_description=FLEXIBLE_REG,
        )
    )
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=registration_number1,
            service_type_description=SCHOOL_OR_WORKS,
        )
    )

    licence_number2 = "PA000002"
    otc_lic2 = LicenceModelFactory(number=licence_number2)
    registration_number2 = f"{licence_number2}/1"
    registration_number3 = f"{licence_number2}/2"
    registration_number6 = f"{licence_number2}/3"
    services_list_1.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number2)
    )
    services_list_1.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number3)
    )
    services_list_1.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number6)
    )

    licence_number3 = "PB000003"
    otc_lic3 = LicenceModelFactory(number=licence_number3)
    registration_number4 = f"{licence_number3}/1"
    registration_number5 = f"{licence_number3}/2"
    # Service created but not adding to the list of services for the LTA
    ServiceModelFactory(licence=otc_lic3, registration_number=registration_number4)
    # Service created but linked to a diffent LTA
    services_list_2.append(
        ServiceModelFactory(licence=otc_lic3, registration_number=registration_number5)
    )

    local_authority_1 = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list_1
    )

    LocalAuthorityFactory(
        id="2", name="second_LTA", registration_numbers=services_list_2
    )

    org1 = OrganisationFactory()
    bods_lic = BODSLicenceFactory(organisation=org1, number=licence_number1)

    # Published but exempted service codes should be included in response
    ServiceCodeExemptionFactory(
        licence=bods_lic, registration_code=int(registration_number6.split("/")[1])
    )

    expected_pairs_org1 = [
        (licence_number1, registration_number1),
        (licence_number2, registration_number2),
        (licence_number2, registration_number6),
        (licence_number2, registration_number3),
    ]

    lta_codes_csv = LTACSV([local_authority_1])
    queryset = lta_codes_csv.get_queryset()

    assert len(queryset) == len(expected_pairs_org1)
    queryset_pairs = [
        (service["otc_licence_number"], service["otc_registration_number"])
        for service in queryset
    ]
    assert sorted(queryset_pairs) == sorted(expected_pairs_org1)


def test_combined_authority_lta_queryset():
    services_list_1 = []
    services_list_2 = []
    licence_number1 = "PD000001"
    otc_lic1 = LicenceModelFactory(number=licence_number1)
    registration_number1 = f"{licence_number1}/1"
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=registration_number1,
            service_type_description=FLEXIBLE_REG,
        )
    )
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=registration_number1,
            service_type_description=SCHOOL_OR_WORKS,
        )
    )

    licence_number2 = "PA000002"
    otc_lic2 = LicenceModelFactory(number=licence_number2)
    registration_number2 = f"{licence_number2}/1"
    registration_number3 = f"{licence_number2}/2"
    registration_number6 = f"{licence_number2}/3"
    services_list_1.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number2)
    )
    services_list_1.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number3)
    )
    services_list_1.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number6)
    )

    licence_number3 = "PB000003"
    otc_lic3 = LicenceModelFactory(number=licence_number3)
    registration_number4 = f"{licence_number3}/1"
    registration_number5 = f"{licence_number3}/2"
    # Service created but not adding to the list of services for the LTA
    ServiceModelFactory(licence=otc_lic3, registration_number=registration_number4)
    # Service created but linked to a diffent LTA
    services_list_2.append(
        ServiceModelFactory(licence=otc_lic3, registration_number=registration_number5)
    )

    local_authority_1 = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list_1
    )

    local_authority_2 = LocalAuthorityFactory(
        id="2", name="second_LTA", registration_numbers=services_list_2
    )

    org1 = OrganisationFactory()
    bods_lic = BODSLicenceFactory(organisation=org1, number=licence_number1)

    # Published but exempted service codes should be included in response
    ServiceCodeExemptionFactory(
        licence=bods_lic, registration_code=int(registration_number6.split("/")[1])
    )

    expected_pairs_org1 = [
        (licence_number1, registration_number1),
        (licence_number2, registration_number2),
        (licence_number2, registration_number6),
        (licence_number2, registration_number3),
        (licence_number3, registration_number5),
    ]

    lta_codes_csv = LTACSV([local_authority_1, local_authority_2])
    queryset = lta_codes_csv.get_queryset()

    assert len(queryset) == len(expected_pairs_org1)
    queryset_pairs = [
        (service["otc_licence_number"], service["otc_registration_number"])
        for service in queryset
    ]
    assert sorted(queryset_pairs) == sorted(expected_pairs_org1)


@freeze_time("2023-02-24")
def test_lta_csv_output():
    services_list_1 = []
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org1 = OrganisationFactory(name="test_org_1")
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)

    # Require Attention: No
    # TXCFileAttribute = None
    # SeasonalService = Not None and Out of Season
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[0],
            service_number=service_numbers[0],
            effective_date=datetime.datetime(2023, 6, 24),
        )
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2024, 2, 24),
        end=datetime.datetime(2026, 2, 24),
    )

    # Require Attention: Yes
    # TXCFileAttribute = None
    # SeasonalService = Not None and In Season
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[1],
            service_number=service_numbers[1],
            effective_date=datetime.datetime(2023, 6, 24),
        )
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[1][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    # Require Attention: No
    # TXCFileAttribute = None
    # Exemption Exists
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[2],
            service_number=service_numbers[2],
            effective_date=datetime.datetime(2023, 6, 24),
        )
    )
    ServiceCodeExemptionFactory(
        licence=bods_licence,
        registration_code=service_codes[2][-1:],
    )

    dataset3 = DatasetFactory(organisation=org1)
    # Require Attention: Yes
    # operating_period_end_date is not None
    TXCFileAttributesFactory(
        revision=dataset3.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[3],
        revision_number="1",
        filename="test3.xml",
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        operating_period_end_date=datetime.datetime(2023, 2, 24),
        modification_datetime=datetime.datetime(2022, 6, 24),
        national_operator_code=national_operator_code,
    )
    # staleness_otc = True => "OTC variation not published"
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[3],
            service_number=service_numbers[3],
            effective_date=datetime.datetime(2023, 3, 24),
        )
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[3][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    dataset4 = DatasetFactory(organisation=org1)
    # Require Attention: Yes
    # operating_period_end_date is not None
    TXCFileAttributesFactory(
        revision=dataset4.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[4],
        filename="test4.xml",
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        operating_period_end_date=datetime.datetime(2023, 3, 24),
        modification_datetime=datetime.datetime(2023, 6, 24),
        national_operator_code=national_operator_code,
    )
    # staleness_42_day_look_ahead = True => "42 day look ahead is incomplete"
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[4],
            service_number=service_numbers[4],
            effective_date=datetime.datetime(2022, 6, 24),
        )
    )
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[4][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    dataset5 = DatasetFactory(organisation=org1)
    # operating_period_end_date is not None
    TXCFileAttributesFactory(
        revision=dataset5.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[5],
        filename="test5.xml",
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        national_operator_code=national_operator_code,
    )
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[5],
            service_number=service_numbers[5],
            effective_date=datetime.datetime(2024, 1, 24),
        )
    )
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[5][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    dataset6 = DatasetFactory(organisation=org1)
    # operating_period_end_date is None
    TXCFileAttributesFactory(
        revision=dataset6.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[6],
        filename="test6.xml",
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
        national_operator_code=national_operator_code,
    )
    # staleness_12_months_old = True => "Service hasn't been updated within a year"
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[6],
            service_number=service_numbers[6],
            effective_date=datetime.datetime(2021, 1, 24),
        )
    )
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[6][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    dataset7 = DatasetFactory(organisation=org1)
    # Require Attention: No
    # operating_period_end_date is None
    TXCFileAttributesFactory(
        revision=dataset7.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[7],
        filename="test7.xml",
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
        national_operator_code=national_operator_code,
    )
    # staleness_12_months_old = True => "Service hasn't been updated within a year"
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[7],
            service_number=service_numbers[7],
            effective_date=datetime.datetime(2021, 1, 24),
        )
    )
    # don't care start end
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[7][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )
    # exemption exists
    ServiceCodeExemptionFactory(
        licence=bods_licence,
        registration_code=service_codes[7][-1:],
    )

    dataset8 = DatasetFactory(organisation=org1)
    # operating_period_end_date is None
    TXCFileAttributesFactory(
        revision=dataset8.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[8],
        filename="test8.xml",
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2023, 2, 24),
        national_operator_code=national_operator_code,
    )
    # staleness_otc = False, stalenes_42_day_look_ahead = False,
    # staleness_12_months_old = False => Up to date
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[8],
            service_number=service_numbers[8],
            effective_date=datetime.datetime(2021, 1, 24),
        )
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[8][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    # Testing something that IS in BODS but not in OTC
    licence_number = "PD0000055"

    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset9 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset9.live_revision,
        licence_number=bods_licence.number,
        operating_period_end_date=None,
        service_code="Z10",
        filename="test9.xml",
        modification_datetime=datetime.datetime(2023, 2, 24),
        national_operator_code=national_operator_code,
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    local_authority_1 = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list_1
    )

    lta_codes_csv = LTACSV([local_authority_1])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    assert [header.strip('"') for header in csv_output["header"]] == csv_columns
    assert csv_output["row0"][0] == '""'  # XML:Service Code
    assert csv_output["row0"][1] == '""'  # XML:Line Name
    assert csv_output["row0"][2] == '"No"'  # Requires Attention
    assert csv_output["row0"][3] == '"Unpublished"'  # Published Status
    assert csv_output["row0"][4] == '"Registered"'  # OTC Status
    assert csv_output["row0"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row0"][6] == '"Out of Season"'  # Seasonal Status
    assert csv_output["row0"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row0"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row0"][9] == '""'  # Dataset ID
    assert csv_output["row0"][10] == '"2023-05-12"'
    # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row0"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row0"][12] == '""'
    # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days,
    assert (
        csv_output["row0"][13] == '"2024-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row0"][14] == '"2024-02-24"'  # Seasonal Start Date
    assert csv_output["row0"][15] == '"2026-02-24"'  # Seasonal End Date
    assert csv_output["row0"][16] == '""'  # XML:Filename
    assert csv_output["row0"][17] == '""'  # XML:Last Modified Date
    assert csv_output["row0"][18] == '""'  # XML:National Operator Code
    assert csv_output["row0"][19] == '""'  # XML:Licence Number
    assert csv_output["row0"][20] == '""'  # XML:Revision Number
    assert csv_output["row0"][21] == '""'  # XML:Operating Period Start Dat
    assert csv_output["row0"][22] == '""'
    # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row0"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row0"][24] == '"PD0000099:0"'  # OTC:Registration Number
    assert csv_output["row0"][25] == '"Line0"'  # OTC Service Number
    assert csv_output["row0"][26] == '""'  # Effective Last Modified Date
    assert csv_output["row0"][27] == '""'
    # effective stale date due to end date:
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row0"][28] == '""'
    # last modified date < Effective stale date due to OTC effective date
    # TXCFileAttributes("effective_stale_date_last_modified_date")
    # < OTCService("effective_stale_date_otc_effective_date")

    assert csv_output["row1"][0] == '""'  # XML:Service Code
    assert csv_output["row1"][1] == '""'  # XML:Line Name
    assert csv_output["row1"][2] == '"Yes"'  # Requires Attention
    assert csv_output["row1"][3] == '"Unpublished"'  # Published Status
    assert csv_output["row1"][4] == '"Registered"'  # OTC Status
    assert csv_output["row1"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row1"][6] == '"In Season"'  # Seasonal Status
    assert csv_output["row1"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row1"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row1"][9] == '""'  # Dataset ID
    assert (
        csv_output["row1"][10] == '"2023-05-12"'
    )  # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row1"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row1"][12] == '""'  # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days,
    assert (
        csv_output["row1"][13] == '"2022-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row1"][14] == '"2022-02-24"'  # Seasonal Start Date
    assert csv_output["row1"][15] == '"2024-02-24"'  # Seasonal End Date
    assert csv_output["row1"][16] == '""'  # XML:Filename
    assert csv_output["row1"][17] == '""'  # XML:Last Modified Date
    assert csv_output["row1"][18] == '""'  # XML:National Operator Code
    assert csv_output["row1"][19] == '""'  # XML:Licence Number
    assert csv_output["row1"][20] == '""'  # XML:Revision Number
    assert csv_output["row1"][21] == '""'  # XML:Operating Period Start Date
    assert csv_output["row1"][22] == '""'  # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row1"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row1"][24] == '"PD0000099:1"'  # OTC:Registration Number
    assert csv_output["row1"][25] == '"Line1"'  # OTC Service Number
    assert csv_output["row1"][26] == '""'  # Effective Last Modified Date
    assert csv_output["row1"][27] == '""'  # effective stale date due to end date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert (
        csv_output["row1"][28] == '""'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 2
    assert csv_output["row2"][0] == '""'  # XML:Service Code
    assert csv_output["row2"][1] == '""'  # XML:Line Name
    assert csv_output["row2"][2] == '"No"'  # Requires Attention
    assert csv_output["row2"][3] == '"Unpublished"'  # Published Status
    assert csv_output["row2"][4] == '"Registered"'  # OTC Status
    assert csv_output["row2"][5] == '"Out of Scope"'  # Scope Status
    assert csv_output["row2"][6] == '"Not Seasonal"'  # Seasonal Status
    assert csv_output["row2"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row2"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row2"][9] == '""'  # Dataset ID
    assert (
        csv_output["row2"][10] == '"2023-05-12"'
    )  # Date OTC variation needs to be published
    assert (
        csv_output["row2"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row2"][12] == '""'  # Date when data is over 1 year old
    assert csv_output["row2"][13] == '""'  # Date seasonal service should be published
    assert csv_output["row2"][14] == '""'  # Seasonal Start Date
    assert csv_output["row2"][15] == '""'  # Seasonal End Date
    assert csv_output["row2"][16] == '""'  # XML:Filename
    assert csv_output["row2"][17] == '""'  # XML:Last Modified Date
    assert csv_output["row2"][18] == '""'  # XML:National Operator Code
    assert csv_output["row2"][19] == '""'  # XML:Licence Number
    assert csv_output["row2"][20] == '""'  # XML:Revision Number
    assert csv_output["row2"][21] == '""'  # XML:Operating Period Start Date
    assert csv_output["row2"][22] == '""'  # XML:Operating Period End Date
    assert csv_output["row2"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row2"][24] == '"PD0000099:2"'  # OTC:Registration Number
    assert csv_output["row2"][25] == '"Line2"'  # OTC Service Number
    assert csv_output["row2"][26] == '""'  # Effective Last Modified Date
    assert csv_output["row2"][27] == '""'  # effective stale date due to end date
    assert (
        csv_output["row2"][28] == '""'
    )  # last modified date < Effective stale date due to OTC effective date

    assert csv_output["row3"][0] == '"PD0000099:3"'  # XML:Service Code
    assert csv_output["row3"][1] == '""'  # XML:Line Name
    assert csv_output["row3"][2] == '"Yes"'  # Requires Attention
    assert csv_output["row3"][3] == '"Published"'  # Published Status
    assert csv_output["row3"][4] == '"Registered"'  # OTC Status
    assert csv_output["row3"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row3"][6] == '"In Season"'  # Seasonal Status
    assert csv_output["row3"][7] == '"OTC variation not published"'  # Timeliness Status
    assert csv_output["row3"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row3"][9] == f'"{dataset3.id}"'  # Dataset ID
    assert (
        csv_output["row3"][10] == '"2023-02-10"'
    )  # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row3"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row3"][12] == '"2023-06-24"'  # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days,
    assert (
        csv_output["row3"][13] == '"2022-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row3"][14] == '"2022-02-24"'  # Seasonal Start Date
    assert csv_output["row3"][15] == '"2024-02-24"'  # Seasonal End Date
    assert csv_output["row3"][16] == '"test3.xml"'  # XML:Filename
    assert csv_output["row3"][17] == '"2022-06-23"'  # XML:Last Modified Date
    assert (
        csv_output["row3"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row3"][19] == '"PD0000099"'  # XML:Licence Number
    assert csv_output["row3"][20] == '"1"'  # XML:Revision Number
    assert csv_output["row3"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row3"][22] == '"2023-02-24"'  # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row3"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row3"][24] == f'"{service_codes[3]}"'  # OTC:Registration Number
    assert csv_output["row3"][25] == f'"{service_numbers[3]}"'  # OTC Service Number
    assert csv_output["row3"][26] == f'"2022-06-23"'  # Effective Last Modified Date
    assert (
        csv_output["row3"][27] == '"2023-01-13"'
    )  # effective stale date due to end date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert (
        csv_output["row3"][28] == '"True"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 4
    assert csv_output["row4"][0] == '"PD0000099:4"'  # XML:Service Code
    assert csv_output["row4"][1] == '""'  # XML:Line Name
    assert csv_output["row4"][2] == '"Yes"'  # Requires Attention
    assert csv_output["row4"][3] == '"Published"'  # Published Status
    assert csv_output["row4"][4] == '"Registered"'  # OTC Status
    assert csv_output["row4"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row4"][6] == '"In Season"'  # Seasonal Status
    assert (
        csv_output["row4"][7] == '"42 day look ahead is incomplete"'
    )  # Timeliness Status
    assert csv_output["row4"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row4"][9] == f'"{dataset4.id}"'  # Dataset ID
    assert (
        csv_output["row4"][10] == '"2022-05-12"'
    )  # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row4"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row4"][12] == '"2024-06-23"'  # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days
    assert (
        csv_output["row4"][13] == '"2022-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row4"][14] == '"2022-02-24"'  # Seasonal Start Date
    assert csv_output["row4"][15] == '"2024-02-24"'  # Seasonal End Date
    assert csv_output["row4"][16] == '"test4.xml"'  # XML:Filename
    assert csv_output["row4"][17] == '"2023-06-23"'  # XML:Last Modified Date
    assert (
        csv_output["row4"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row4"][19] == '"PD0000099"'  # XML:Licence Number
    assert csv_output["row4"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row4"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row4"][22] == '"2023-03-24"'  # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row4"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row4"][24] == f'"{service_codes[4]}"'  # OTC:Registration Number
    assert csv_output["row4"][25] == f'"{service_numbers[4]}"'  # OTC Service Number
    assert csv_output["row4"][26] == f'"2023-06-23"'  # Effective Last Modified Date
    assert (
        csv_output["row4"][27] == '"2023-02-10"'
    )  # effective stale date due to end date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert (
        csv_output["row4"][28] == '"False"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 5
    assert csv_output["row5"][0] == '"PD0000099:5"'  # XML:Service Code
    assert csv_output["row5"][1] == '""'  # XML:Line Name
    assert csv_output["row5"][2] == '"No"'  # Requires Attention
    assert csv_output["row5"][3] == '"Published"'  # Published Status
    assert csv_output["row5"][4] == '"Registered"'  # OTC Status
    assert csv_output["row5"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row5"][6] == '"In Season"'  # Seasonal Status
    assert csv_output["row5"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row5"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row5"][9] == f'"{dataset5.id}"'  # Dataset ID
    assert (
        csv_output["row5"][10] == '"2023-12-13"'
    )  # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row5"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row5"][12] == '"2023-01-24"'  # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days
    assert (
        csv_output["row5"][13] == '"2022-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row5"][14] == '"2022-02-24"'  # Seasonal Start Date
    assert csv_output["row5"][15] == '"2024-02-24"'  # Seasonal End Date
    assert csv_output["row5"][16] == '"test5.xml"'  # XML:Filename
    assert csv_output["row5"][17] == '"2022-01-24"'  # XML:Last Modified Date
    assert (
        csv_output["row5"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row5"][19] == '"PD0000099"'  # XML:Licence Number
    assert csv_output["row5"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row5"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row5"][22] == '"2023-06-24"'  # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row5"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row5"][24] == f'"{service_codes[5]}"'  # OTC:Registration Number
    assert csv_output["row5"][25] == f'"{service_numbers[5]}"'  # OTC Service Number
    assert csv_output["row5"][26] == f'"2022-01-24"'  # Effective Last Modified Date
    assert (
        csv_output["row5"][27] == '"2023-05-12"'
    )  # effective stale date due to end date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert (
        csv_output["row5"][28] == '"True"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 6
    assert csv_output["row6"][0] == '"PD0000099:6"'  # XML:Service Code
    assert csv_output["row6"][1] == '""'  # XML:Line Name
    assert csv_output["row6"][2] == '"Yes"'  # Requires Attention
    assert csv_output["row6"][3] == '"Published"'  # Published Status
    assert csv_output["row6"][4] == '"Registered"'  # OTC Status
    assert csv_output["row6"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row6"][6] == '"In Season"'  # Seasonal Status
    assert (
        csv_output["row6"][7] == '"Service hasn\'t been updated within a year"'
    )  # Timeliness Status
    assert csv_output["row6"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row6"][9] == f'"{dataset6.id}"'  # Dataset ID
    assert (
        csv_output["row6"][10] == '"2020-12-13"'
    )  # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row6"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row6"][12] == '"2023-01-24"'  # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days
    assert (
        csv_output["row6"][13] == '"2022-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row6"][14] == '"2022-02-24"'  # Seasonal Start Date
    assert csv_output["row6"][15] == '"2024-02-24"'  # Seasonal End Date
    assert csv_output["row6"][16] == '"test6.xml"'  # XML:Filename
    assert csv_output["row6"][17] == '"2022-01-24"'  # XML:Last Modified Date
    assert (
        csv_output["row6"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row6"][19] == '"PD0000099"'  # XML:Licence Number
    assert csv_output["row6"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row6"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row6"][22] == '""'  # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row6"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row6"][24] == f'"{service_codes[6]}"'  # OTC:Registration Number
    assert csv_output["row6"][25] == f'"{service_numbers[6]}"'  # OTC Service Number
    assert csv_output["row6"][26] == f'"2022-01-24"'  # Effective Last Modified Date
    assert csv_output["row6"][27] == '""'  # effective stale date due to end date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert (
        csv_output["row6"][28] == '"False"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 7
    assert csv_output["row7"][0] == '"PD0000099:7"'  # XML:Service Code
    assert csv_output["row7"][1] == '""'  # XML:Line Name
    assert csv_output["row7"][2] == '"No"'  # Requires Attention
    assert csv_output["row7"][3] == '"Published"'  # Published Status
    assert csv_output["row7"][4] == '"Registered"'  # OTC Status
    assert csv_output["row7"][5] == '"Out of Scope"'  # Scope Status
    assert csv_output["row7"][6] == '"In Season"'  # Seasonal Status
    assert (
        csv_output["row7"][7] == '"Service hasn\'t been updated within a year"'
    )  # Timeliness Status
    assert csv_output["row7"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row7"][9] == f'"{dataset7.id}"'  # Dataset ID
    assert (
        csv_output["row7"][10] == '"2020-12-13"'
    )  # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row7"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row7"][12] == '"2023-01-24"'  # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days
    assert (
        csv_output["row7"][13] == '"2022-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row7"][14] == '"2022-02-24"'  # Seasonal Start Date
    assert csv_output["row7"][15] == '"2024-02-24"'  # Seasonal End Date
    assert csv_output["row7"][16] == '"test7.xml"'  # XML:Filename
    assert csv_output["row7"][17] == '"2022-01-24"'  # XML:Last Modified Date
    assert (
        csv_output["row7"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row7"][19] == '"PD0000099"'  # XML:Licence Number
    assert csv_output["row7"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row7"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row7"][22] == '""'  # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row7"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row7"][24] == f'"{service_codes[7]}"'  # OTC:Registration Number
    assert csv_output["row7"][25] == f'"{service_numbers[7]}"'  # OTC Service Number
    assert csv_output["row7"][26] == f'"2022-01-24"'  # Effective Last Modified Date
    assert csv_output["row7"][27] == '""'  # effective stale date due to end date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert (
        csv_output["row7"][28] == '"False"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 8
    print(csv_output["row8"])
    assert csv_output["row8"][0] == '"PD0000099:8"'  # XML:Service Code
    assert csv_output["row8"][1] == '""'  # XML:Line Name
    assert csv_output["row8"][2] == '"No"'  # Requires Attention
    assert csv_output["row8"][3] == '"Published"'  # Published Status
    assert csv_output["row8"][4] == '"Registered"'  # OTC Status
    assert csv_output["row8"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row8"][6] == '"In Season"'  # Seasonal Status
    assert csv_output["row8"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row8"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row8"][9] == f'"{dataset8.id}"'  # Dataset ID
    assert (
        csv_output["row8"][10] == '"2020-12-13"'
    )  # Date OTC variation needs to be published
    # OTCService("effective_date") - 42 days
    assert (
        csv_output["row8"][11] == '"2023-04-07"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row8"][12] == '"2024-02-24"'  # Date when data is over 1 year old
    # TXCFileAttributes("modification_datetime") + 365 days
    assert (
        csv_output["row8"][13] == '"2022-01-13"'
    )  # Date seasonal service should be published
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row8"][14] == '"2022-02-24"'  # Seasonal Start Date
    assert csv_output["row8"][15] == '"2024-02-24"'  # Seasonal End Date
    assert csv_output["row8"][16] == '"test8.xml"'  # XML:Filename
    assert csv_output["row8"][17] == '"2023-02-24"'  # XML:Last Modified Date
    assert (
        csv_output["row8"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row8"][19] == '"PD0000099"'  # XML:Licence Number
    assert csv_output["row8"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row8"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row8"][22] == '""'  # XML:Operating Period End Date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row8"][23] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row8"][24] == f'"{service_codes[8]}"'  # OTC:Registration Number
    assert csv_output["row8"][25] == f'"{service_numbers[8]}"'  # OTC Service Number
    assert csv_output["row8"][26] == f'"2023-02-24"'  # Effective Last Modified Date
    assert csv_output["row8"][27] == '""'  # effective stale date due to end date
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert (
        csv_output["row8"][28] == '"False"'
    )  # last modified date < Effective stale date due to OTC effective date


def test_lta_csv_output_unpublished_status_no_organisation_name():
    services_list_1 = []
    licence_number = "PD0000099"
    licence_number_two = "PD0000098"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org1 = OrganisationFactory(name="test_org_1")
    BODSLicenceFactory(organisation=org1, number=licence_number_two)

    otc_lic = LicenceModelFactory(id=10, number=licence_number)
    service1 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[0],
        service_number=service_numbers[0],
        effective_date=datetime.datetime(2023, 6, 24),
    )
    services_list_1.append(service1)

    local_authority_1 = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list_1
    )

    lta_codes_csv = LTACSV([local_authority_1])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    assert csv_output["row0"][3] == '"Unpublished"'  # published status
    assert csv_output["row0"][8] == '"Organisation not yet created"'  # Operator Name


@freeze_time("2023-02-28")
def test_seasonal_status_lta_csv_output():
    services_list_1 = []
    licence_number = "PD0001111"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org = OrganisationFactory(name="test_org_1")
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)

    # Up to date
    dataset0 = DatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset0.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[0],
        filename="test0.xml",
        operating_period_end_date=datetime.datetime(2023, 6, 28),
        modification_datetime=datetime.datetime(2022, 1, 28),
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        national_operator_code=national_operator_code,
    )
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[0],
            service_number=service_numbers[0],
            effective_date=datetime.datetime(2024, 1, 28),
        )
    )
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2022, 2, 28),
        end=datetime.datetime(2024, 2, 28),
    )

    dataset1 = DatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[1],
        filename="test1.xml",
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        national_operator_code=national_operator_code,
    )
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[1],
            service_number=service_numbers[1],
            effective_date=datetime.datetime(2024, 1, 24),
        )
    )
    # out of season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[1][-1:],
        start=datetime.datetime(2026, 2, 28),
        end=datetime.datetime(2028, 2, 28),
    )

    # Not Seasonal
    dataset2 = DatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset2.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[2],
        filename="test2.xml",
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        national_operator_code=national_operator_code,
    )
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[2],
            service_number=service_numbers[2],
            effective_date=datetime.datetime(2024, 1, 24),
        )
    )

    dataset3 = DatasetFactory(organisation=org)
    # operating_period_end_date is None
    TXCFileAttributesFactory(
        revision=dataset3.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[3],
        filename="test3.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 28),
        operating_period_start_date=datetime.datetime(1999, 6, 26),
        national_operator_code=national_operator_code,
    )
    # is_stale: staleness_12_months_old = True => "Service hasn't been updated within a year"
    services_list_1.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[3],
            service_number=service_numbers[3],
            effective_date=datetime.datetime(2021, 1, 28),
        )
    )
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[3][-1:],
        start=datetime.datetime(2022, 2, 28),
        end=datetime.datetime(2024, 2, 28),
    )

    local_authority_1 = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list_1
    )

    lta_codes_csv = LTACSV([local_authority_1])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    # Row 0
    assert csv_output["row0"][0] == '"PD0001111:0"'  # XML:Service Code
    assert csv_output["row0"][1] == '""'  # XML:Line Name
    assert csv_output["row0"][2] == '"No"'  # Requires Attention
    assert csv_output["row0"][3] == '"Published"'  # Published Status
    assert csv_output["row0"][4] == '"Registered"'  # OTC Status
    assert csv_output["row0"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row0"][6] == '"In Season"'  # Seasonal Status
    assert csv_output["row0"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row0"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row0"][9] == f'"{dataset0.id}"'  # Dataset ID
    assert (
        csv_output["row0"][10] == '"2023-12-17"'
    )  # Date OTC variation needs to be published
    assert (
        csv_output["row0"][11] == '"2023-04-11"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row0"][12] == '"2023-01-28"'  # Date when data is over 1 year old
    assert (
        csv_output["row0"][13] == '"2022-01-17"'
    )  # Date seasonal service should be published
    assert csv_output["row0"][14] == '"2022-02-28"'  # Seasonal Start Date
    assert csv_output["row0"][15] == '"2024-02-28"'  # Seasonal End Date
    assert csv_output["row0"][16] == '"test0.xml"'  # XML:Filename
    assert csv_output["row0"][17] == '"2022-01-28"'  # XML:Last Modified Date
    assert (
        csv_output["row0"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row0"][19] == '"PD0001111"'  # XML:Licence Number
    assert csv_output["row0"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row0"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row0"][22] == '"2023-06-28"'  # XML:Operating Period End Date
    assert csv_output["row0"][23] == '"PD0001111"'  # OTC:Licence Number
    assert csv_output["row0"][24] == '"PD0001111:0"'  # OTC:Registration Number
    assert csv_output["row0"][25] == '"Line0"'  # OTC Service Number
    assert csv_output["row0"][26] == '"2022-01-28"'  # Effective Last Modified Date
    assert (
        csv_output["row0"][27] == '"2023-05-16"'
    )  # effective stale date due to end date
    assert (
        csv_output["row0"][28] == '"True"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 1
    assert csv_output["row1"][0] == '"PD0001111:1"'  # XML:Service Code
    assert csv_output["row1"][1] == '""'  # XML:Line Name
    assert csv_output["row1"][2] == '"No"'  # Requires Attention
    assert csv_output["row1"][3] == '"Published"'  # Published Status
    assert csv_output["row1"][4] == '"Registered"'  # OTC Status
    assert csv_output["row1"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row1"][6] == '"Out of Season"'  # Seasonal Status
    assert csv_output["row1"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row1"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row1"][9] == f'"{dataset1.id}"'  # Dataset ID
    assert (
        csv_output["row1"][10] == '"2023-12-13"'
    )  # Date OTC variation needs to be published
    assert (
        csv_output["row1"][11] == '"2023-04-11"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row1"][12] == '"2023-01-24"'  # Date when data is over 1 year old
    assert (
        csv_output["row1"][13] == '"2026-01-17"'
    )  # Date seasonal service should be published
    assert csv_output["row1"][14] == '"2026-02-28"'  # Seasonal Start Date
    assert csv_output["row1"][15] == '"2028-02-28"'  # Seasonal End Date
    assert csv_output["row1"][16] == '"test1.xml"'  # XML:Filename
    assert csv_output["row1"][17] == '"2022-01-24"'  # XML:Last Modified Date
    assert (
        csv_output["row1"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row1"][19] == '"PD0001111"'  # XML:Licence Number
    assert csv_output["row1"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row1"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row1"][22] == '"2023-06-24"'  # XML:Operating Period End Date
    assert csv_output["row1"][23] == '"PD0001111"'  # OTC:Licence Number
    assert csv_output["row1"][24] == '"PD0001111:1"'  # OTC:Registration Number
    assert csv_output["row1"][25] == '"Line1"'  # OTC Service Number
    assert csv_output["row1"][26] == '"2022-01-24"'  # Effective Last Modified Date
    assert (
        csv_output["row1"][27] == '"2023-05-12"'
    )  # effective stale date due to end date
    assert (
        csv_output["row1"][28] == '"True"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 2
    assert csv_output["row2"][0] == '"PD0001111:2"'  # XML:Service Code
    assert csv_output["row2"][1] == '""'  # XML:Line Name
    assert csv_output["row2"][2] == '"No"'  # Requires Attention
    assert csv_output["row2"][3] == '"Published"'  # Published Status
    assert csv_output["row2"][4] == '"Registered"'  # OTC Status
    assert csv_output["row2"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row2"][6] == '"Not Seasonal"'  # Seasonal Status
    assert csv_output["row2"][7] == '"Up to date"'  # Timeliness Status
    assert csv_output["row2"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row2"][9] == f'"{dataset2.id}"'  # Dataset ID
    assert (
        csv_output["row2"][10] == '"2023-12-13"'
    )  # Date OTC variation needs to be published
    assert (
        csv_output["row2"][11] == '"2023-04-11"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row2"][12] == '"2023-01-24"'  # Date when data is over 1 year old
    assert csv_output["row2"][13] == '""'  # Date seasonal service should be published
    assert csv_output["row2"][14] == '""'  # Seasonal Start Date
    assert csv_output["row2"][15] == '""'  # Seasonal End Date
    assert csv_output["row2"][16] == '"test2.xml"'  # XML:Filename
    assert csv_output["row2"][17] == '"2022-01-24"'  # XML:Last Modified Date
    assert (
        csv_output["row2"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row2"][19] == '"PD0001111"'  # XML:Licence Number
    assert csv_output["row2"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row2"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row2"][22] == '"2023-06-24"'  # XML:Operating Period End Date
    assert csv_output["row2"][23] == '"PD0001111"'  # OTC:Licence Number
    assert csv_output["row2"][24] == '"PD0001111:2"'  # OTC:Registration Number
    assert csv_output["row2"][25] == '"Line2"'  # OTC Service Number
    assert csv_output["row2"][26] == '"2022-01-24"'  # Effective Last Modified Date
    assert (
        csv_output["row2"][27] == '"2023-05-12"'
    )  # effective stale date due to end date
    assert (
        csv_output["row2"][28] == '"True"'
    )  # last modified date < Effective stale date due to OTC effective date

    # Row 3
    assert csv_output["row3"][0] == '"PD0001111:3"'  # XML:Service Code
    assert csv_output["row3"][1] == '""'  # XML:Line Name
    assert csv_output["row3"][2] == '"Yes"'  # Requires Attention
    assert csv_output["row3"][3] == '"Published"'  # Published Status
    assert csv_output["row3"][4] == '"Registered"'  # OTC Status
    assert csv_output["row3"][5] == '"In Scope"'  # Scope Status
    assert csv_output["row3"][6] == '"In Season"'  # Seasonal Status
    assert (
        csv_output["row3"][7] == '"Service hasn\'t been updated within a year"'
    )  # Timeliness Status
    assert csv_output["row3"][8] == '"test_org_1"'  # Organisation Name
    assert csv_output["row3"][9] == f'"{dataset3.id}"'  # Dataset ID
    assert (
        csv_output["row3"][10] == '"2020-12-17"'
    )  # Date OTC variation needs to be published
    assert (
        csv_output["row3"][11] == '"2023-04-11"'
    )  # Date for complete 42-day look ahead
    assert csv_output["row3"][12] == '"2023-01-28"'  # Date when data is over 1 year old
    assert (
        csv_output["row3"][13] == '"2022-01-17"'
    )  # Date seasonal service should be published
    assert csv_output["row3"][14] == '"2022-02-28"'  # Seasonal Start Date
    assert csv_output["row3"][15] == '"2024-02-28"'  # Seasonal End Date
    assert csv_output["row3"][16] == '"test3.xml"'  # XML:Filename
    assert csv_output["row3"][17] == '"2022-01-28"'  # XML:Last Modified Date
    assert (
        csv_output["row3"][18] == f'"{national_operator_code}"'
    )  # XML:National Operator Code
    assert csv_output["row3"][19] == '"PD0001111"'  # XML:Licence Number
    assert csv_output["row3"][20] == '"0"'  # XML:Revision Number
    assert csv_output["row3"][21] == '"1999-06-26"'  # XML:Operating Period Start Date
    assert csv_output["row3"][22] == '""'  # XML:Operating Period End Date
    assert csv_output["row3"][23] == '"PD0001111"'  # OTC:Licence Number
    assert csv_output["row3"][24] == '"PD0001111:3"'  # OTC:Registration Number
    assert csv_output["row3"][25] == '"Line3"'  # OTC Service Number
    assert csv_output["row3"][26] == '"2022-01-28"'  # Effective Last Modified Date
    assert csv_output["row3"][27] == '""'  # effective stale date due to end date
    assert (
        csv_output["row3"][28] == '"False"'
    )  # last modified date < Effective stale date due to OTC effective date
