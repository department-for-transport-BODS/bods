from typing import Dict

import faker
import pytest
from django.db.models.expressions import datetime
from freezegun import freeze_time

from transit_odp.browse.lta_column_headers import header_accessor_data_compliance_report
from transit_odp.browse.views.local_authority import LTAComplianceReportCSV
from transit_odp.naptan.factories import AdminAreaFactory
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
    UILtaFactory,
)

pytestmark = pytest.mark.django_db
FAKER = faker.Faker()
csv_line_level_columns = [
    header for header, _ in header_accessor_data_compliance_report
]
CSV_LINE_LEVEL_NUMBER_COLUMNS = len(csv_line_level_columns)
national_operator_code = "".join(FAKER.random_letters(length=4)).upper()


def get_csv_output(csv_string: str, number_of_columns: int) -> Dict[str, list]:
    result_list = csv_string.replace("\r\n", ",").split(",")[:-1]
    result = {}
    len_result_list = len(result_list)
    start = 0
    i = 0
    result.update({"header": result_list[start:number_of_columns]})
    start += number_of_columns
    for end in range(2 * number_of_columns, len_result_list + 1, number_of_columns):
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

    lta_codes_csv = LTAComplianceReportCSV([local_authority_1])
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

    lta_codes_csv = LTAComplianceReportCSV([local_authority_1, local_authority_2])
    queryset = lta_codes_csv.get_queryset()

    assert len(queryset) == len(expected_pairs_org1)
    queryset_pairs = [
        (service["otc_licence_number"], service["otc_registration_number"])
        for service in queryset
    ]
    assert sorted(queryset_pairs) == sorted(expected_pairs_org1)


@freeze_time("2023-02-24")
def test_lta_line_level_columns_order():
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

    ui_lta = UILtaFactory(name="UI_LTA")

    local_authority_1 = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list_1, ui_lta=ui_lta
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    lta_codes_csv = LTAComplianceReportCSV([local_authority_1])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string, CSV_LINE_LEVEL_NUMBER_COLUMNS)
    actual_columns = [header.strip('"') for header in csv_output["header"]]

    assert actual_columns[0] == "Registration:Registration Number"
    assert actual_columns[1] == "Registration:Service Number"
    assert actual_columns[2] == "Registration Status"
    assert actual_columns[3] == "Scope Status"
    assert actual_columns[4] == "Seasonal Status"
    assert actual_columns[5] == "Organisation Name"
    assert actual_columns[6] == "Requires Attention"
    assert actual_columns[7] == "Timetables requires attention"
    assert actual_columns[8] == "Timetables Published Status"
    assert actual_columns[9] == "Timetables Timeliness Status"
    assert actual_columns[10] == "Timetables critical DQ issues"
    assert actual_columns[11] == "AVL requires attention"
    assert actual_columns[12] == "AVL Published Status"
    assert actual_columns[13] == "AVL to Timetable Match Status"
    assert actual_columns[14] == "Fares requires attention"
    assert actual_columns[15] == "Fares Published Status"
    assert actual_columns[16] == "Fares Timeliness Status"
    assert actual_columns[17] == "Fares Compliance Status"
    assert actual_columns[18] == "Timetables Data set ID"
    assert actual_columns[19] == "TXC:Filename"
    assert actual_columns[20] == "TXC:NOC"
    assert actual_columns[21] == "TXC:Last Modified Date"
    assert actual_columns[22] == "Date when timetable data is over 1 year old"
    assert actual_columns[23] == "TXC:Operating Period End Date"
    assert actual_columns[24] == "Fares Data set ID"
    assert actual_columns[25] == "NETEX:Filename"
    assert actual_columns[26] == "NETEX:Last Modified Date"
    assert actual_columns[27] == "Date when fares data is over 1 year old"
    assert actual_columns[28] == "NETEX:Operating Period End Date"
    assert actual_columns[29] == "Date Registration variation needs to be published"
    assert actual_columns[30] == "Date for complete 42 day look ahead"
    assert actual_columns[31] == "Date seasonal service should be published"
    assert actual_columns[32] == "Seasonal Start Date"
    assert actual_columns[33] == "Seasonal End Date"
    assert actual_columns[34] == "Registration:Operator Name"
    assert actual_columns[35] == "Registration:Licence Number"
    assert actual_columns[36] == "Registration:Service Type Description"
    assert actual_columns[37] == "Registration:Variation Number"
    assert actual_columns[38] == "Registration:Expiry Date"
    assert actual_columns[39] == "Registration:Effective Date"
    assert actual_columns[40] == "Registration:Received Date"
    assert actual_columns[41] == "Traveline Region"
    assert actual_columns[42] == "Local Transport Authority"


@freeze_time("2023-02-24")
def test_lta_line_level_csv():
    services_list_1 = []
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]
    operator_factory = OperatorModelFactory(operator_name="operator")
    org1 = OrganisationFactory(name="test_org_1")
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)

    # Require Attention: No
    # TXCFileAttribute = None
    # SeasonalService = Not None and Out of Season
    service_1 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[0],
        service_number=service_numbers[0],
        effective_date=datetime.datetime(2023, 6, 24),
        variation_number=11,
        start_point="start point service 1",
        finish_point="finish point service 1",
        via="via service 1",
        service_type_other_details="service type detail service 1",
        description="description service 1",
        operator=operator_factory,
        service_type_description="service type description service 1",
    )
    services_list_1.append(service_1)
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2024, 2, 24),
        end=datetime.datetime(2026, 2, 24),
    )

    # Require Attention: Yes
    # TXCFileAttribute = None
    # SeasonalService = Not None and In Season
    service_2 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[1],
        service_number=service_numbers[1],
        effective_date=datetime.datetime(2023, 6, 24),
        variation_number=22,
        start_point="start point service 2",
        finish_point="finish point service 2",
        via="via service 2",
        service_type_other_details="service type detail service 2",
        description="description service 2",
        operator=operator_factory,
        service_type_description="service type description service 2",
    )
    services_list_1.append(service_2)
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[1][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    # Require Attention: No
    # TXCFileAttribute = None
    # Exemption Exists
    service_3 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[2],
        service_number=service_numbers[2],
        effective_date=datetime.datetime(2023, 6, 24),
        variation_number=33,
        start_point="start point service 3",
        finish_point="finish point service 3",
        via="via service 3",
        service_type_other_details="service type detail service 3",
        description="description service 3",
        operator=operator_factory,
        service_type_description="service type description service 3",
    )
    services_list_1.append(service_3)
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
    service_4 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[3],
        service_number=service_numbers[3],
        effective_date=datetime.datetime(2023, 3, 24),
        variation_number=44,
        start_point="start point service 4",
        finish_point="finish point service 4",
        via="via service 4",
        service_type_other_details="service type detail service 4",
        description="description service 4",
        operator=operator_factory,
        service_type_description="service type description service 4",
    )
    services_list_1.append(service_4)
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
    service_5 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[4],
        service_number=service_numbers[4],
        effective_date=datetime.datetime(2022, 6, 24),
        variation_number=55,
        start_point="start point service 5",
        finish_point="finish point service 5",
        via="via service 5",
        service_type_other_details="service type detail service 5",
        description="description service 5",
        operator=operator_factory,
        service_type_description="service type description service 5",
    )
    services_list_1.append(service_5)
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
    service_6 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[5],
        service_number=service_numbers[5],
        effective_date=datetime.datetime(2024, 1, 24),
        variation_number=66,
        start_point="start point service 6",
        finish_point="finish point service 6",
        via="via service 6",
        service_type_other_details="service type detail service 6",
        description="description service 6",
        operator=operator_factory,
        service_type_description="service type description service 6",
    )
    services_list_1.append(service_6)
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
    service_7 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[6],
        service_number=service_numbers[6],
        effective_date=datetime.datetime(2021, 1, 24),
        variation_number=77,
        start_point="start point service 7",
        finish_point="finish point service 7",
        via="via service 7",
        service_type_other_details="service type detail service 7",
        description="description service 7",
        operator=operator_factory,
        service_type_description="service type description service 7",
    )
    services_list_1.append(service_7)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[6][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    local_authority_1 = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list_1, ui_lta=ui_lta
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    lta_codes_csv = LTAComplianceReportCSV([local_authority_1])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string, CSV_LINE_LEVEL_NUMBER_COLUMNS)

    assert csv_output["row0"][0] == '"PD0000099:0"'
    assert csv_output["row0"][1] == '"Line0"'
    assert csv_output["row0"][2] == '"Registered"'
    assert csv_output["row0"][3] == '"In Scope"'
    assert csv_output["row0"][4] == '"Out of Season"'
    assert csv_output["row0"][5] == '"test_org_1"'
    assert csv_output["row0"][6] == '"No"'
    assert csv_output["row0"][7] == '"No"'
    assert csv_output["row0"][8] == '"Unpublished"'
    assert csv_output["row0"][9] == '"Up to date"'
    assert csv_output["row0"][10] == '"Under maintenance"'
    assert csv_output["row0"][11] == '"Yes"'
    assert csv_output["row0"][12] == '"No"'
    assert csv_output["row0"][13] == '"No"'
    assert csv_output["row0"][14] == '"Under maintenance"'
    assert csv_output["row0"][15] == '"Under maintenance"'
    assert csv_output["row0"][16] == '"Under maintenance"'
    assert csv_output["row0"][17] == '"Under maintenance"'
    assert csv_output["row0"][18] == '""'
    assert csv_output["row0"][19] == '""'
    assert csv_output["row0"][20] == '""'
    assert csv_output["row0"][21] == '""'
    assert csv_output["row0"][22] == '""'
    assert csv_output["row0"][23] == '""'
    assert csv_output["row0"][24] == '"Under maintenance"'
    assert csv_output["row0"][25] == '"Under maintenance"'
    assert csv_output["row0"][26] == '"Under maintenance"'
    assert csv_output["row0"][27] == '"Under maintenance"'
    assert csv_output["row0"][28] == '"Under maintenance"'
    assert csv_output["row0"][29] == '"2023-05-12"'
    assert csv_output["row0"][30] == '"2023-04-07"'
    assert csv_output["row0"][31] == '"2024-01-13"'
    assert csv_output["row0"][32] == '"2024-02-24"'
    assert csv_output["row0"][33] == '"2026-02-24"'
    assert csv_output["row0"][34] == '"operator"'
    assert csv_output["row0"][35] == '"PD0000099"'
    assert csv_output["row0"][36] == '"service type description service 1"'
    assert csv_output["row0"][37] == '"11"'
    assert csv_output["row0"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row0"][39] == '"2023-06-24"'
    assert csv_output["row0"][40] == f'"{service_1.received_date}"'
    assert csv_output["row0"][41] == '"South East"'
    assert csv_output["row0"][42] == '"UI_LTA"'

    assert csv_output["row1"][0] == '"PD0000099:1"'
    assert csv_output["row1"][1] == '"Line1"'
    assert csv_output["row1"][2] == '"Registered"'
    assert csv_output["row1"][3] == '"In Scope"'
    assert csv_output["row1"][4] == '"In Season"'
    assert csv_output["row1"][5] == '"test_org_1"'
    assert csv_output["row1"][6] == '"Yes"'
    assert csv_output["row1"][7] == '"Yes"'
    assert csv_output["row1"][8] == '"Unpublished"'
    assert csv_output["row1"][9] == '"Up to date"'
    assert csv_output["row1"][10] == '"Under maintenance"'
    assert csv_output["row1"][11] == '"Yes"'
    assert csv_output["row1"][12] == '"No"'
    assert csv_output["row1"][13] == '"No"'
    assert csv_output["row1"][14] == '"Under maintenance"'
    assert csv_output["row1"][15] == '"Under maintenance"'
    assert csv_output["row1"][16] == '"Under maintenance"'
    assert csv_output["row1"][17] == '"Under maintenance"'
    assert csv_output["row1"][18] == '""'
    assert csv_output["row1"][19] == '""'
    assert csv_output["row1"][20] == '""'
    assert csv_output["row1"][21] == '""'
    assert csv_output["row1"][22] == '""'
    assert csv_output["row1"][23] == '""'
    assert csv_output["row1"][24] == '"Under maintenance"'
    assert csv_output["row1"][25] == '"Under maintenance"'
    assert csv_output["row1"][26] == '"Under maintenance"'
    assert csv_output["row1"][27] == '"Under maintenance"'
    assert csv_output["row1"][28] == '"Under maintenance"'
    assert csv_output["row1"][29] == '"2023-05-12"'
    assert csv_output["row1"][30] == '"2023-04-07"'
    assert csv_output["row1"][31] == '"2022-01-13"'
    assert csv_output["row1"][32] == '"2022-02-24"'
    assert csv_output["row1"][33] == '"2024-02-24"'
    assert csv_output["row1"][34] == '"operator"'
    assert csv_output["row1"][35] == '"PD0000099"'
    assert csv_output["row1"][36] == '"service type description service 2"'
    assert csv_output["row1"][37] == '"22"'
    assert csv_output["row1"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row1"][39] == '"2023-06-24"'
    assert csv_output["row1"][40] == f'"{service_2.received_date}"'
    assert csv_output["row1"][41] == '"South East"'
    assert csv_output["row1"][42] == '"UI_LTA"'

    assert csv_output["row2"][0] == '"PD0000099:2"'
    assert csv_output["row2"][1] == '"Line2"'
    assert csv_output["row2"][2] == '"Registered"'
    assert csv_output["row2"][3] == '"Out of Scope"'
    assert csv_output["row2"][4] == '"Not Seasonal"'
    assert csv_output["row2"][5] == '"test_org_1"'
    assert csv_output["row2"][6] == '"No"'
    assert csv_output["row2"][7] == '"No"'
    assert csv_output["row2"][8] == '"Unpublished"'
    assert csv_output["row2"][9] == '"Up to date"'
    assert csv_output["row2"][10] == '"Under maintenance"'
    assert csv_output["row2"][11] == '"Yes"'
    assert csv_output["row2"][12] == '"No"'
    assert csv_output["row2"][13] == '"No"'
    assert csv_output["row2"][14] == '"Under maintenance"'
    assert csv_output["row2"][15] == '"Under maintenance"'
    assert csv_output["row2"][16] == '"Under maintenance"'
    assert csv_output["row2"][17] == '"Under maintenance"'
    assert csv_output["row2"][18] == '""'
    assert csv_output["row2"][19] == '""'
    assert csv_output["row2"][20] == '""'
    assert csv_output["row2"][21] == '""'
    assert csv_output["row2"][22] == '""'
    assert csv_output["row2"][23] == '""'
    assert csv_output["row2"][24] == '"Under maintenance"'
    assert csv_output["row2"][25] == '"Under maintenance"'
    assert csv_output["row2"][26] == '"Under maintenance"'
    assert csv_output["row2"][27] == '"Under maintenance"'
    assert csv_output["row2"][28] == '"Under maintenance"'
    assert csv_output["row2"][29] == '"2023-05-12"'
    assert csv_output["row2"][30] == '"2023-04-07"'
    assert csv_output["row2"][31] == '""'
    assert csv_output["row2"][32] == '""'
    assert csv_output["row2"][33] == '""'
    assert csv_output["row2"][34] == '"operator"'
    assert csv_output["row2"][35] == '"PD0000099"'
    assert csv_output["row2"][36] == '"service type description service 3"'
    assert csv_output["row2"][37] == '"33"'
    assert csv_output["row2"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row2"][39] == '"2023-06-24"'
    assert csv_output["row2"][40] == f'"{service_3.received_date}"'
    assert csv_output["row2"][41] == '"South East"'
    assert csv_output["row2"][42] == '"UI_LTA"'

    assert csv_output["row3"][0] == '"PD0000099:3"'
    assert csv_output["row3"][1] == '"Line3"'
    assert csv_output["row3"][2] == '"Registered"'
    assert csv_output["row3"][3] == '"In Scope"'
    assert csv_output["row3"][4] == '"In Season"'
    assert csv_output["row3"][5] == '"test_org_1"'
    assert csv_output["row3"][6] == '"Yes"'
    assert csv_output["row3"][7] == '"Yes"'
    assert csv_output["row3"][8] == '"Unpublished"'
    assert csv_output["row3"][9] == '"Up to date"'
    assert csv_output["row3"][10] == '"Under maintenance"'
    assert csv_output["row3"][11] == '"Yes"'
    assert csv_output["row3"][12] == '"No"'
    assert csv_output["row3"][13] == '"No"'
    assert csv_output["row3"][14] == '"Under maintenance"'
    assert csv_output["row3"][15] == '"Under maintenance"'
    assert csv_output["row3"][16] == '"Under maintenance"'
    assert csv_output["row3"][17] == '"Under maintenance"'
    assert csv_output["row3"][18] == '""'
    assert csv_output["row3"][19] == '""'
    assert csv_output["row3"][20] == '""'
    assert csv_output["row3"][21] == '""'
    assert csv_output["row3"][22] == '""'
    assert csv_output["row3"][23] == '""'
    assert csv_output["row3"][24] == '"Under maintenance"'
    assert csv_output["row3"][25] == '"Under maintenance"'
    assert csv_output["row3"][26] == '"Under maintenance"'
    assert csv_output["row3"][27] == '"Under maintenance"'
    assert csv_output["row3"][28] == '"Under maintenance"'
    assert csv_output["row3"][29] == '"2023-02-10"'
    assert csv_output["row3"][30] == '"2023-04-07"'
    assert csv_output["row3"][31] == '"2022-01-13"'
    assert csv_output["row3"][32] == '"2022-02-24"'
    assert csv_output["row3"][33] == '"2024-02-24"'
    assert csv_output["row3"][34] == '"operator"'
    assert csv_output["row3"][35] == '"PD0000099"'
    assert csv_output["row3"][36] == '"service type description service 4"'
    assert csv_output["row3"][37] == '"44"'
    assert csv_output["row3"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row3"][39] == '"2023-03-24"'
    assert csv_output["row3"][40] == f'"{service_4.received_date}"'
    assert csv_output["row3"][41] == '"South East"'
    assert csv_output["row3"][42] == '"UI_LTA"'

    assert csv_output["row4"][0] == '"PD0000099:4"'
    assert csv_output["row4"][1] == '"Line4"'
    assert csv_output["row4"][2] == '"Registered"'
    assert csv_output["row4"][3] == '"In Scope"'
    assert csv_output["row4"][4] == '"In Season"'
    assert csv_output["row4"][5] == '"test_org_1"'
    assert csv_output["row4"][6] == '"Yes"'
    assert csv_output["row4"][7] == '"Yes"'
    assert csv_output["row4"][8] == '"Unpublished"'
    assert csv_output["row4"][9] == '"Up to date"'
    assert csv_output["row4"][10] == '"Under maintenance"'
    assert csv_output["row4"][11] == '"Yes"'
    assert csv_output["row4"][12] == '"No"'
    assert csv_output["row4"][13] == '"No"'
    assert csv_output["row4"][14] == '"Under maintenance"'
    assert csv_output["row4"][15] == '"Under maintenance"'
    assert csv_output["row4"][16] == '"Under maintenance"'
    assert csv_output["row4"][17] == '"Under maintenance"'
    assert csv_output["row4"][18] == '""'
    assert csv_output["row4"][19] == '""'
    assert csv_output["row4"][20] == '""'
    assert csv_output["row4"][21] == '""'
    assert csv_output["row4"][22] == '""'
    assert csv_output["row4"][23] == '""'
    assert csv_output["row4"][24] == '"Under maintenance"'
    assert csv_output["row4"][25] == '"Under maintenance"'
    assert csv_output["row4"][26] == '"Under maintenance"'
    assert csv_output["row4"][27] == '"Under maintenance"'
    assert csv_output["row4"][28] == '"Under maintenance"'
    assert csv_output["row4"][29] == '"2022-05-12"'
    assert csv_output["row4"][30] == '"2023-04-07"'
    assert csv_output["row4"][31] == '"2022-01-13"'
    assert csv_output["row4"][32] == '"2022-02-24"'
    assert csv_output["row4"][33] == '"2024-02-24"'
    assert csv_output["row4"][34] == '"operator"'
    assert csv_output["row4"][35] == '"PD0000099"'
    assert csv_output["row4"][36] == '"service type description service 5"'
    assert csv_output["row4"][37] == '"55"'
    assert csv_output["row4"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row4"][39] == '"2022-06-24"'
    assert csv_output["row4"][40] == f'"{service_5.received_date}"'
    assert csv_output["row4"][41] == '"South East"'
    assert csv_output["row4"][42] == '"UI_LTA"'

    assert csv_output["row5"][0] == '"PD0000099:5"'
    assert csv_output["row5"][1] == '"Line5"'
    assert csv_output["row5"][2] == '"Registered"'
    assert csv_output["row5"][3] == '"In Scope"'
    assert csv_output["row5"][4] == '"In Season"'
    assert csv_output["row5"][5] == '"test_org_1"'
    assert csv_output["row5"][6] == '"Yes"'
    assert csv_output["row5"][7] == '"Yes"'
    assert csv_output["row5"][8] == '"Unpublished"'
    assert csv_output["row5"][9] == '"Up to date"'
    assert csv_output["row5"][10] == '"Under maintenance"'
    assert csv_output["row5"][11] == '"Yes"'
    assert csv_output["row5"][12] == '"No"'
    assert csv_output["row5"][13] == '"No"'
    assert csv_output["row5"][14] == '"Under maintenance"'
    assert csv_output["row5"][15] == '"Under maintenance"'
    assert csv_output["row5"][16] == '"Under maintenance"'
    assert csv_output["row5"][17] == '"Under maintenance"'
    assert csv_output["row5"][18] == '""'
    assert csv_output["row5"][19] == '""'
    assert csv_output["row5"][20] == '""'
    assert csv_output["row5"][21] == '""'
    assert csv_output["row5"][22] == '""'
    assert csv_output["row5"][23] == '""'
    assert csv_output["row5"][24] == '"Under maintenance"'
    assert csv_output["row5"][25] == '"Under maintenance"'
    assert csv_output["row5"][26] == '"Under maintenance"'
    assert csv_output["row5"][27] == '"Under maintenance"'
    assert csv_output["row5"][28] == '"Under maintenance"'
    assert csv_output["row5"][29] == '"2023-12-13"'
    assert csv_output["row5"][30] == '"2023-04-07"'
    assert csv_output["row5"][31] == '"2022-01-13"'
    assert csv_output["row5"][32] == '"2022-02-24"'
    assert csv_output["row5"][33] == '"2024-02-24"'
    assert csv_output["row5"][34] == '"operator"'
    assert csv_output["row5"][35] == '"PD0000099"'
    assert csv_output["row5"][36] == '"service type description service 6"'
    assert csv_output["row5"][37] == '"66"'
    assert csv_output["row5"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row5"][39] == '"2024-01-24"'
    assert csv_output["row5"][40] == f'"{service_6.received_date}"'
    assert csv_output["row5"][41] == '"South East"'
    assert csv_output["row5"][42] == '"UI_LTA"'

    assert csv_output["row6"][0] == '"PD0000099:6"'
    assert csv_output["row6"][1] == '"Line6"'
    assert csv_output["row6"][2] == '"Registered"'
    assert csv_output["row6"][3] == '"In Scope"'
    assert csv_output["row6"][4] == '"In Season"'
    assert csv_output["row6"][5] == '"test_org_1"'
    assert csv_output["row6"][6] == '"Yes"'
    assert csv_output["row6"][7] == '"Yes"'
    assert csv_output["row6"][8] == '"Unpublished"'
    assert csv_output["row6"][9] == '"Up to date"'
    assert csv_output["row6"][10] == '"Under maintenance"'
    assert csv_output["row6"][11] == '"Yes"'
    assert csv_output["row6"][12] == '"No"'
    assert csv_output["row6"][13] == '"No"'
    assert csv_output["row6"][14] == '"Under maintenance"'
    assert csv_output["row6"][15] == '"Under maintenance"'
    assert csv_output["row6"][16] == '"Under maintenance"'
    assert csv_output["row6"][17] == '"Under maintenance"'
    assert csv_output["row6"][18] == '""'
    assert csv_output["row6"][19] == '""'
    assert csv_output["row6"][20] == '""'
    assert csv_output["row6"][21] == '""'
    assert csv_output["row6"][22] == '""'
    assert csv_output["row6"][23] == '""'
    assert csv_output["row6"][24] == '"Under maintenance"'
    assert csv_output["row6"][25] == '"Under maintenance"'
    assert csv_output["row6"][26] == '"Under maintenance"'
    assert csv_output["row6"][27] == '"Under maintenance"'
    assert csv_output["row6"][28] == '"Under maintenance"'
    assert csv_output["row6"][29] == '"2020-12-13"'
    assert csv_output["row6"][30] == '"2023-04-07"'
    assert csv_output["row6"][31] == '"2022-01-13"'
    assert csv_output["row6"][32] == '"2022-02-24"'
    assert csv_output["row6"][33] == '"2024-02-24"'
    assert csv_output["row6"][34] == '"operator"'
    assert csv_output["row6"][35] == '"PD0000099"'
    assert csv_output["row6"][36] == '"service type description service 7"'
    assert csv_output["row6"][37] == '"77"'
    assert csv_output["row6"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row6"][39] == '"2021-01-24"'
    assert csv_output["row6"][40] == f'"{service_7.received_date}"'
    assert csv_output["row6"][41] == '"South East"'
    assert csv_output["row6"][42] == '"UI_LTA"'


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

    lta_codes_csv = LTAComplianceReportCSV([local_authority_1])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string, CSV_LINE_LEVEL_NUMBER_COLUMNS)

    assert csv_output["row0"][5] == '"Organisation not yet created"'  # Operator Name
    assert csv_output["row0"][8] == '"Unpublished"'  # published status


@freeze_time("2023-02-24")
def test_timeliness_status_42_day_look_ahead():
    """
    Test for 'Timetables Timeliness Status' column logic:

    Staleness Status - Stale - 42 Day Look Ahead:
        If Operating period end date is present
        AND
        Staleness status is not OTC Variation
        AND
        Operating period end date < today + 42 days
    """
    services_list = []
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org = OrganisationFactory()
    otc_lic = LicenceModelFactory(number=licence_number)

    dataset_one = DatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset_one.live_revision,
        service_code=service_codes[4],
        licence_number=otc_lic.number,
        filename="test4.xml",
        operating_period_end_date=datetime.datetime(2023, 3, 24),
        modification_datetime=datetime.datetime(2023, 1, 24),
        line_names=[service_numbers[4]],
    )

    services_list.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[4],
            service_number=service_numbers[4],
            effective_date=datetime.datetime(2022, 6, 24),
        )
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    local_authority = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list, ui_lta=ui_lta
    )

    lta_codes_csv = LTAComplianceReportCSV([local_authority])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string, CSV_LINE_LEVEL_NUMBER_COLUMNS)
    actual_values = [row.strip('"') for row in csv_output["row0"]]

    assert "42 day look ahead is incomplete" in actual_values


@freeze_time("2023-02-24")
def test_timeliness_status_12_months_old():
    """
    Test for 'Timetables Timeliness Status' column logic:

    Staleness Status - Stale - 12 months old:
        If Staleness status is not OTC Variation
        AND
        Staleness status is not 42 day look ahead
        AND
        last_modified + 365 days <= today
    """
    services_list = []
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org = OrganisationFactory()
    otc_lic = LicenceModelFactory(number=licence_number)

    dataset6 = DatasetFactory(organisation=org)
    # operating_period_end_date is None
    TXCFileAttributesFactory(
        revision=dataset6.live_revision,
        service_code=service_codes[6],
        licence_number=otc_lic.number,
        filename="test6.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[6]],
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
    services_list.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[6],
            service_number=service_numbers[6],
            effective_date=datetime.datetime(2021, 1, 24),
        )
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    local_authority = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list, ui_lta=ui_lta
    )

    lta_codes_csv = LTAComplianceReportCSV([local_authority])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string, CSV_LINE_LEVEL_NUMBER_COLUMNS)
    actual_values = [row.strip('"') for row in csv_output["row0"]]

    assert "Service hasn't been updated within a year" in actual_values


@freeze_time("2023-02-24")
def test_timeliness_status_otc_variation():
    """
    Test for 'Timetables Timeliness Status' column logic:

    Staleness Status - Stale - OTC Variation:
        Staleness Status - Stale - OTC Variation
        When Associated data is No
        AND
        today >= Effective stale date due to OTC effective date
        NB: Associated data is Yes IF
        (last modified date >= Association date due to OTC effective date
        OR Operating period start date = OTC effective date).
    """
    services_list = []
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org = OrganisationFactory()
    otc_lic = LicenceModelFactory(number=licence_number)

    dataset_one = DatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset_one.live_revision,
        service_code=service_codes[3],
        licence_number=otc_lic.number,
        filename="test3.xml",
        operating_period_end_date=datetime.datetime(2023, 2, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[3]],
    )

    services_list.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[3],
            service_number=service_numbers[3],
            effective_date=datetime.datetime(2023, 3, 24),
        )
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    local_authority = LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services_list, ui_lta=ui_lta
    )

    lta_codes_csv = LTAComplianceReportCSV([local_authority])
    csv_string = lta_codes_csv.to_string()
    csv_output = get_csv_output(csv_string, CSV_LINE_LEVEL_NUMBER_COLUMNS)
    actual_values = [row.strip('"') for row in csv_output["row0"]]

    assert "OTC variation not published" in actual_values
