from typing import Dict

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
    OperatorModelFactory,
    ServiceModelFactory,
)

pytestmark = pytest.mark.django_db
CSV_NUMBER_COLUMNS = 27


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
        operating_period_end_date=datetime.datetime(2023, 2, 24),
        modification_datetime=datetime.datetime(2022, 6, 24),
    )
    # staleness_otc = True => "Stale - OTC Variation"
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
        operating_period_end_date=datetime.datetime(2023, 3, 24),
        modification_datetime=datetime.datetime(2023, 6, 24),
    )
    # staleness_end_date = True => "Stale - End date passed"
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
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
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
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
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
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
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
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2023, 2, 24),
    )
    # staleness_otc = False, staleness_end_date = False,
    # staleness_12_months_old = False => Not Stale
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
    )

    # Testing something that IS in BODS but not in OTC
    licence_number = "PD0000055"

    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset8 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset8.live_revision,
        licence_number=bods_licence.number,
        operating_period_end_date=None,
        service_code="Z10",
        filename="test9.xml",
        modification_datetime=datetime.datetime(2023, 2, 24),
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

    assert csv_output["header"] == [
        '"Requires Attention"',
        '"Published Status"',
        '"OTC Status"',
        '"Scope Status"',
        '"Seasonal Status"',
        '"Staleness Status"',
        '"Operator Name"',
        '"Data set Licence Number"',
        '"Data set Service Code"',
        '"Data set Line Name"',
        '"Operating Period Start Date"',
        '"Operating Period End Date"',
        '"OTC Licence Number"',
        '"OTC Registration Number"',
        '"OTC Service Number"',
        '"Data set Revision Number"',
        '"Last Modified Date"',
        '"Effective Last Modified Date"',
        '"XML Filename"',
        '"Dataset ID"',
        '"Effective Seasonal Start Date"',
        '"Seasonal Start Date"',
        '"Seasonal End Date"',
        '"Effective stale date due to end date"',
        '"Effective stale date due to Effective last modified date"',
        '"Last modified date < Effective stale date due to OTC effective date"',
        '"Effective stale date due to OTC effective date"',
    ]
    assert csv_output["row0"][0] == '"No"'  # requires attention
    assert csv_output["row0"][1] == '"Unpublished"'  # published status
    assert csv_output["row0"][2] == '"Registered"'  # OTC status
    assert csv_output["row0"][3] == '"In Scope"'  # scope status
    assert csv_output["row0"][4] == '"Out of Season"'  # seasonal status
    assert csv_output["row0"][5] == '"Not Stale"'  # staleness status
    assert csv_output["row0"][6] == '"Organisation not yet created"'  # Operator Name
    assert csv_output["row0"][7] == '""'  # Dataset Licence Number
    assert csv_output["row0"][8] == '""'  # Dataset Service Code
    assert csv_output["row0"][9] == '""'  # Dataset Line Name
    assert csv_output["row0"][10] == '""'  # Operating Period Start Date
    assert csv_output["row0"][11] == '""'  # Operating Period End Date
    assert csv_output["row0"][12] == '"PD0000099"'  # OTC Licence Number
    assert csv_output["row0"][13] == '"PD0000099:0"'  # OTC Registration Number
    assert csv_output["row0"][14] == '"Line0"'  # OTC Service Number
    assert csv_output["row0"][15] == '""'  # Dataset Revision Number
    assert csv_output["row0"][16] == '""'  # Last Modified Date
    assert csv_output["row0"][17] == '""'  # Effective Last Modified Date
    assert csv_output["row0"][18] == '""'  # XML Filename
    assert csv_output["row0"][19] == '""'  # dataset id
    assert csv_output["row0"][20] == '"2024-01-13"'
    # effective seasonal start: SeasonalService("start") - 42 days
    assert csv_output["row0"][21] == '"2024-02-24"'  # seasonal start date
    assert csv_output["row0"][22] == '"2026-02-24"'  # seasonal end date
    assert csv_output["row0"][23] == '""'
    # effective stale date due to end date:
    # TXCFileAttributes("operationg_period_end_date") - 42 days
    assert csv_output["row0"][24] == '""'
    # effective stale date due to effective last modified date:
    # TXCFileAttributes("modification_datetime") + 365 days,
    assert csv_output["row0"][25] == '""'
    # last modified date < Effective stale date due to OTC effective date
    # TXCFileAttributes("effective_stale_date_last_modified_date")
    # < OTCService("effective_stale_date_otc_effective_date")
    assert csv_output["row0"][26] == '"2023-05-12"'
    # effective stale date due to OTC effective date
    # OTCService("effective_date") - 42 days

    assert csv_output["row1"][0] == '"Yes"'
    assert csv_output["row1"][1] == '"Unpublished"'
    assert csv_output["row1"][2] == '"Registered"'
    assert csv_output["row1"][3] == '"In Scope"'
    assert csv_output["row1"][4] == '"In Season"'
    assert csv_output["row1"][5] == '"Not Stale"'
    assert csv_output["row1"][6] == '"Organisation not yet created"'
    assert csv_output["row1"][7] == '""'
    assert csv_output["row1"][8] == '""'
    assert csv_output["row1"][9] == '""'
    assert csv_output["row1"][12] == '"PD0000099"'
    assert csv_output["row1"][13] == '"PD0000099:1"'
    assert csv_output["row1"][14] == '"Line1"'
    assert csv_output["row1"][15] == '""'
    assert csv_output["row1"][16] == '""'
    assert csv_output["row1"][20] == '"2022-01-13"'
    assert csv_output["row1"][21] == '"2022-02-24"'
    assert csv_output["row1"][22] == '"2024-02-24"'
    assert csv_output["row1"][23] == '""'
    assert csv_output["row1"][24] == '""'
    assert csv_output["row1"][25] == '""'
    assert csv_output["row1"][26] == '"2023-05-12"'

    assert csv_output["row2"][0] == '"No"'
    assert csv_output["row2"][1] == '"Unpublished"'
    assert csv_output["row2"][2] == '"Registered"'
    assert csv_output["row2"][3] == '"Out of Scope"'
    assert csv_output["row2"][4] == '"Not Seasonal"'
    assert csv_output["row2"][5] == '"Not Stale"'
    assert csv_output["row2"][6] == '"Organisation not yet created"'
    assert csv_output["row2"][7] == '""'
    assert csv_output["row2"][8] == '""'
    assert csv_output["row2"][9] == '""'
    assert csv_output["row2"][12] == '"PD0000099"'
    assert csv_output["row2"][13] == '"PD0000099:2"'
    assert csv_output["row2"][14] == '"Line2"'
    assert csv_output["row2"][16] == '""'
    assert csv_output["row2"][26] == '"2023-05-12"'

    assert csv_output["row3"][0] == '"Yes"'
    assert csv_output["row3"][1] == '"Published"'
    assert csv_output["row3"][2] == '"Registered"'
    assert csv_output["row3"][3] == '"In Scope"'
    assert csv_output["row3"][4] == '"In Season"'
    assert csv_output["row3"][5] == '"Stale - OTC Variation"'
    assert csv_output["row3"][6] == '"test_org_1"'
    assert csv_output["row3"][7] == '"PD0000099"'
    assert csv_output["row3"][8] == '"PD0000099:3"'
    assert csv_output["row3"][9] == '""'
    assert csv_output["row3"][11] == '"2023-02-24"'
    assert csv_output["row3"][12] == '"PD0000099"'
    assert csv_output["row3"][13] == '"PD0000099:3"'
    assert csv_output["row3"][14] == '"Line3"'
    assert csv_output["row3"][15] == '"1"'
    assert csv_output["row3"][16] == '"2022-06-23"'
    assert csv_output["row3"][17] == '"2022-06-23"'
    assert csv_output["row3"][18] == '"test3.xml"'
    assert csv_output["row3"][19] == f'"{dataset3.id}"'
    assert csv_output["row3"][20] == '"2022-01-13"'
    assert csv_output["row3"][21] == '"2022-02-24"'
    assert csv_output["row3"][22] == '"2024-02-24"'
    assert csv_output["row3"][23] == '"2023-01-13"'
    assert csv_output["row3"][24] == '"2023-06-24"'
    assert csv_output["row3"][25] == '"True"'
    assert csv_output["row3"][26] == '"2023-02-10"'

    assert csv_output["row4"][0] == '"Yes"'
    assert csv_output["row4"][1] == '"Published"'
    assert csv_output["row4"][2] == '"Registered"'
    assert csv_output["row4"][3] == '"In Scope"'
    assert csv_output["row4"][4] == '"In Season"'
    assert csv_output["row4"][5] == '"Stale - End date passed"'
    assert csv_output["row4"][6] == '"test_org_1"'
    assert csv_output["row4"][7] == '"PD0000099"'
    assert csv_output["row4"][8] == '"PD0000099:4"'
    assert csv_output["row4"][9] == '""'
    assert csv_output["row3"][11] == '"2023-02-24"'
    assert csv_output["row4"][12] == '"PD0000099"'
    assert csv_output["row4"][13] == '"PD0000099:4"'
    assert csv_output["row4"][14] == '"Line4"'
    assert csv_output["row4"][16] == '"2023-06-23"'
    assert csv_output["row4"][17] == '"2023-06-23"'
    assert csv_output["row4"][19] == f'"{dataset4.id}"'
    assert csv_output["row4"][24] == '"2024-06-23"'
    assert csv_output["row4"][25] == '"False"'
    assert csv_output["row4"][26] == '"2022-05-12"'

    assert csv_output["row5"][0] == '"No"'
    assert csv_output["row5"][1] == '"Published"'
    assert csv_output["row5"][2] == '"Registered"'
    assert csv_output["row5"][3] == '"In Scope"'
    assert csv_output["row5"][5] == '"Not Stale"'
    assert csv_output["row5"][6] == '"test_org_1"'
    assert csv_output["row5"][7] == '"PD0000099"'
    assert csv_output["row5"][8] == '"PD0000099:5"'
    assert csv_output["row5"][9] == '""'
    assert csv_output["row5"][11] == '"2023-06-24"'
    assert csv_output["row5"][12] == '"PD0000099"'
    assert csv_output["row5"][13] == '"PD0000099:5"'
    assert csv_output["row5"][14] == '"Line5"'
    assert csv_output["row5"][19] == f'"{dataset5.id}"'
    assert csv_output["row5"][24] == '"2023-01-24"'
    assert csv_output["row5"][25] == '"True"'
    assert csv_output["row5"][26] == '"2023-12-13"'

    assert csv_output["row6"][0] == '"Yes"'
    assert csv_output["row6"][1] == '"Published"'
    assert csv_output["row6"][2] == '"Registered"'
    assert csv_output["row6"][3] == '"In Scope"'
    assert csv_output["row6"][5] == '"Stale - 12 months old"'
    assert csv_output["row6"][6] == '"test_org_1"'
    assert csv_output["row6"][7] == '"PD0000099"'
    assert csv_output["row6"][8] == '"PD0000099:6"'
    assert csv_output["row6"][9] == '""'
    assert csv_output["row6"][11] == '""'
    assert csv_output["row6"][12] == '"PD0000099"'
    assert csv_output["row6"][13] == '"PD0000099:6"'
    assert csv_output["row6"][14] == '"Line6"'
    assert csv_output["row6"][19] == f'"{dataset6.id}"'
    assert csv_output["row6"][21] == '"2022-02-24"'
    assert csv_output["row6"][22] == '"2024-02-24"'
    assert csv_output["row6"][24] == '"2023-01-24"'
    assert csv_output["row6"][25] == '"False"'
    assert csv_output["row6"][26] == '"2020-12-13"'

    assert csv_output["row7"][0] == '"No"'
    assert csv_output["row7"][1] == '"Published"'
    assert csv_output["row7"][2] == '"Registered"'
    assert csv_output["row7"][3] == '"Out of Scope"'
    assert csv_output["row7"][5] == '"Stale - 12 months old"'
    assert csv_output["row7"][6] == '"test_org_1"'
    assert csv_output["row7"][7] == '"PD0000099"'
    assert csv_output["row7"][8] == '"PD0000099:7"'
    assert csv_output["row7"][9] == '""'
    assert csv_output["row7"][11] == '""'
    assert csv_output["row7"][12] == '"PD0000099"'
    assert csv_output["row7"][13] == '"PD0000099:7"'
    assert csv_output["row7"][14] == '"Line7"'
    assert csv_output["row7"][24] == '"2023-01-24"'
    assert csv_output["row7"][25] == '"False"'
    assert csv_output["row7"][26] == '"2020-12-13"'

    assert csv_output["row8"][0] == '"No"'
    assert csv_output["row8"][1] == '"Published"'
    assert csv_output["row8"][2] == '"Registered"'
    assert csv_output["row8"][3] == '"In Scope"'
    assert csv_output["row8"][5] == '"Not Stale"'
    assert csv_output["row8"][6] == '"test_org_1"'
    assert csv_output["row8"][7] == '"PD0000099"'
    assert csv_output["row8"][8] == '"PD0000099:8"'
    assert csv_output["row8"][9] == '""'
    assert csv_output["row8"][11] == '""'
    assert csv_output["row8"][12] == '"PD0000099"'
    assert csv_output["row8"][13] == '"PD0000099:8"'
    assert csv_output["row8"][14] == '"Line8"'
    assert csv_output["row8"][24] == '"2024-02-24"'
    assert csv_output["row8"][25] == '"False"'
    assert csv_output["row8"][26] == '"2020-12-13"'


def test_lta_csv_output_unpublished_status_operator_name():
    services_list_1 = []
    licence_number = "PD0000099"
    otc_operator_name = "test_org_1"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    otc_lic = LicenceModelFactory(id=10, number=licence_number)
    otc_operator = OperatorModelFactory(id=1, operator_name=otc_operator_name)
    service1 = ServiceModelFactory(
        operator=otc_operator,
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

    assert csv_output["row0"][1] == '"Unpublished"'  # published status
    assert csv_output["row0"][6] == '"test_org_1"'  # Operator Name


def test_lta_csv_output_unpublished_status_no_operator_name():
    services_list_1 = []
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

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

    assert csv_output["row0"][1] == '"Unpublished"'  # published status
    assert csv_output["row0"][6] == '"Organisation not yet created"'  # Operator Name


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

    # Not Stale
    dataset0 = DatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset0.live_revision,
        licence_number=otc_lic.number,
        service_code=service_codes[0],
        filename="test0.xml",
        operating_period_end_date=datetime.datetime(2023, 6, 28),
        modification_datetime=datetime.datetime(2022, 1, 28),
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
    )
    # is_stale: staleness_12_months_old = True => "Stale - 12 months old"
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

    assert csv_output["row0"][0] == '"No"'
    assert csv_output["row0"][1] == '"Published"'
    assert csv_output["row0"][2] == '"Registered"'
    assert csv_output["row0"][3] == '"In Scope"'
    assert csv_output["row0"][4] == '"In Season"'
    assert csv_output["row0"][5] == '"Not Stale"'
    assert csv_output["row0"][6] == '"test_org_1"'
    assert csv_output["row0"][7] == f'"{licence_number}"'
    assert csv_output["row0"][8] == f'"{licence_number}:0"'
    assert csv_output["row0"][9] == '""'
    assert csv_output["row0"][11] == '"2023-06-28"'
    assert csv_output["row0"][12] == f'"{licence_number}"'
    assert csv_output["row0"][13] == f'"{licence_number}:0"'
    assert csv_output["row0"][14] == '"Line0"'
    assert csv_output["row0"][16] == '"2022-01-28"'
    assert csv_output["row0"][17] == '"2022-01-28"'
    assert csv_output["row0"][18] == '"test0.xml"'
    assert csv_output["row0"][19] == f'"{dataset0.id}"'
    assert csv_output["row0"][20] == '"2022-01-17"'
    assert csv_output["row0"][21] == '"2022-02-28"'
    assert csv_output["row0"][22] == '"2024-02-28"'
    assert csv_output["row0"][23] == '"2023-05-16"'
    assert csv_output["row0"][24] == '"2023-01-28"'
    assert csv_output["row0"][25] == '"True"'
    assert csv_output["row0"][26] == '"2023-12-17"'

    assert csv_output["row1"][0] == '"No"'
    assert csv_output["row1"][1] == '"Published"'
    assert csv_output["row1"][2] == '"Registered"'
    assert csv_output["row1"][3] == '"In Scope"'
    assert csv_output["row1"][4] == '"Out of Season"'
    assert csv_output["row1"][5] == '"Not Stale"'
    assert csv_output["row1"][6] == '"test_org_1"'
    assert csv_output["row1"][7] == f'"{licence_number}"'
    assert csv_output["row1"][8] == f'"{licence_number}:1"'
    assert csv_output["row1"][9] == '""'
    assert csv_output["row1"][11] == '"2023-06-24"'
    assert csv_output["row1"][12] == f'"{licence_number}"'
    assert csv_output["row1"][13] == f'"{licence_number}:1"'
    assert csv_output["row1"][14] == '"Line1"'
    assert csv_output["row1"][16] == '"2022-01-24"'
    assert csv_output["row1"][17] == '"2022-01-24"'
    assert csv_output["row1"][18] == '"test1.xml"'
    assert csv_output["row1"][19] == f'"{dataset1.id}"'
    assert csv_output["row1"][20] == '"2026-01-17"'
    assert csv_output["row1"][21] == '"2026-02-28"'
    assert csv_output["row1"][22] == '"2028-02-28"'
    assert csv_output["row1"][23] == '"2023-05-12"'
    assert csv_output["row1"][24] == '"2023-01-24"'
    assert csv_output["row1"][25] == '"True"'
    assert csv_output["row1"][26] == '"2023-12-13"'

    assert csv_output["row2"][0] == '"No"'
    assert csv_output["row2"][1] == '"Published"'
    assert csv_output["row2"][2] == '"Registered"'
    assert csv_output["row2"][3] == '"In Scope"'
    assert csv_output["row2"][4] == '"Not Seasonal"'
    assert csv_output["row2"][5] == '"Not Stale"'
    assert csv_output["row2"][6] == '"test_org_1"'
    assert csv_output["row2"][7] == f'"{licence_number}"'
    assert csv_output["row2"][8] == f'"{licence_number}:2"'
    assert csv_output["row2"][9] == '""'
    assert csv_output["row2"][11] == '"2023-06-24"'
    assert csv_output["row2"][12] == f'"{licence_number}"'
    assert csv_output["row2"][13] == f'"{licence_number}:2"'
    assert csv_output["row2"][14] == '"Line2"'
    assert csv_output["row2"][16] == '"2022-01-24"'
    assert csv_output["row2"][17] == '"2022-01-24"'
    assert csv_output["row2"][18] == '"test2.xml"'
    assert csv_output["row2"][19] == f'"{dataset2.id}"'
    assert csv_output["row2"][20] == '""'
    assert csv_output["row2"][21] == '""'
    assert csv_output["row2"][22] == '""'
    assert csv_output["row2"][23] == '"2023-05-12"'
    assert csv_output["row2"][24] == '"2023-01-24"'
    assert csv_output["row2"][25] == '"True"'
    assert csv_output["row2"][26] == '"2023-12-13"'

    assert csv_output["row3"][0] == '"Yes"'
    assert csv_output["row3"][1] == '"Published"'
    assert csv_output["row3"][2] == '"Registered"'
    assert csv_output["row3"][3] == '"In Scope"'
    assert csv_output["row3"][4] == '"In Season"'
    assert csv_output["row3"][5] == '"Stale - 12 months old"'
    assert csv_output["row3"][6] == '"test_org_1"'
    assert csv_output["row3"][7] == f'"{licence_number}"'
    assert csv_output["row3"][8] == f'"{licence_number}:3"'
    assert csv_output["row3"][9] == '""'
    assert csv_output["row3"][12] == f'"{licence_number}"'
    assert csv_output["row3"][13] == f'"{licence_number}:3"'
    assert csv_output["row3"][14] == '"Line3"'
    assert csv_output["row3"][16] == '"2022-01-28"'
    assert csv_output["row3"][17] == '"2022-01-28"'
    assert csv_output["row3"][18] == '"test3.xml"'
    assert csv_output["row3"][19] == f'"{dataset3.id}"'
    assert csv_output["row3"][20] == '"2022-01-17"'
    assert csv_output["row3"][21] == '"2022-02-28"'
    assert csv_output["row3"][22] == '"2024-02-28"'
    assert csv_output["row3"][23] == '""'
    assert csv_output["row3"][24] == '"2023-01-28"'
    assert csv_output["row3"][25] == '"False"'
    assert csv_output["row3"][26] == '"2020-12-17"'
