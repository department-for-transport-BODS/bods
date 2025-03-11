from datetime import timedelta
from typing import Dict

import pytest
from django.db.models.expressions import datetime
from freezegun import freeze_time
from waffle.testutils import override_flag

from transit_odp.fares.factories import (
    DataCatalogueMetaDataFactory,
    FaresMetadataFactory,
)
from transit_odp.fares_validator.factories import FaresValidationResultFactory
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.constants import FaresType
from transit_odp.organisation.csv.service_codes import ComplianceReportCSV
from transit_odp.organisation.factories import (
    DatasetFactory,
    FaresDatasetRevisionFactory,
)
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    SeasonalServiceFactory,
    ServiceCodeExemptionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.constants import API_TYPE_WECA, FLEXIBLE_REG, SCHOOL_OR_WORKS
from transit_odp.otc.factories import (
    LicenceModelFactory,
    LocalAuthorityFactory,
    OperatorModelFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.common.constants import FeatureFlags

pytestmark = pytest.mark.django_db
CSV_NUMBER_COLUMNS = 43


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


def test_queryset():
    licence_number1 = "PD000001"
    otc_lic1 = LicenceModelFactory(number=licence_number1)
    registration_number1 = f"{licence_number1}/1"
    weca_registration_number1 = f"{licence_number1}/01010001"
    atco_code = "010"
    api_type = API_TYPE_WECA
    services = []
    # otc services
    services.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=registration_number1,
            service_type_description=FLEXIBLE_REG,
        )
    )
    services.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=registration_number1,
            service_type_description=SCHOOL_OR_WORKS,
        )
    )
    # weca services
    services.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=weca_registration_number1,
            service_type_description=FLEXIBLE_REG,
            api_type=api_type,
            atco_code=atco_code,
        )
    )
    services.append(
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=weca_registration_number1,
            service_type_description=SCHOOL_OR_WORKS,
            api_type=api_type,
            atco_code=atco_code,
        )
    )

    licence_number2 = "PA000002"
    otc_lic2 = LicenceModelFactory(number=licence_number2)
    registration_number2 = f"{licence_number2}/1"
    registration_number3 = f"{licence_number2}/2"
    registration_number6 = f"{licence_number2}/3"

    weca_registration_number2 = f"{licence_number2}/01010001"
    weca_registration_number3 = f"{licence_number2}/01010002"
    weca_registration_number6 = f"{licence_number2}/01010003"
    # otc services
    services.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number2)
    )
    services.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number3)
    )
    services.append(
        ServiceModelFactory(licence=otc_lic2, registration_number=registration_number6)
    )
    # weca services
    services.append(
        ServiceModelFactory(
            licence=otc_lic2,
            registration_number=weca_registration_number2,
            api_type=api_type,
            atco_code=atco_code,
        )
    )
    services.append(
        ServiceModelFactory(
            licence=otc_lic2,
            registration_number=weca_registration_number3,
            api_type=api_type,
            atco_code=atco_code,
        )
    )
    services.append(
        ServiceModelFactory(
            licence=otc_lic2,
            registration_number=weca_registration_number6,
            api_type=api_type,
            atco_code=atco_code,
        )
    )

    licence_number3 = "PB000003"
    otc_lic3 = LicenceModelFactory(number=licence_number3)
    # otc services
    registration_number4 = f"{licence_number3}/1"
    registration_number5 = f"{licence_number3}/2"
    services.append(
        ServiceModelFactory(licence=otc_lic3, registration_number=registration_number4)
    )
    services.append(
        ServiceModelFactory(licence=otc_lic3, registration_number=registration_number5)
    )

    # weca services
    weca_registration_number4 = f"{licence_number3}/01010001"
    weca_registration_number5 = f"{licence_number3}/01010002"
    services.append(
        ServiceModelFactory(
            licence=otc_lic3, registration_number=weca_registration_number4
        )
    )
    services.append(
        ServiceModelFactory(
            licence=otc_lic3, registration_number=weca_registration_number5
        )
    )

    org1 = OrganisationFactory()
    BODSLicenceFactory(organisation=org1, number=licence_number1)
    bods_lic = BODSLicenceFactory(organisation=org1, number=licence_number2)
    org2 = OrganisationFactory()
    BODSLicenceFactory(organisation=org2, number=licence_number3)

    ui_lta = UILtaFactory(name="UI_LTA")

    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

    # Published but exempted service codes should be included in response
    ServiceCodeExemptionFactory(
        licence=bods_lic, registration_code=int(registration_number6.split("/")[1])
    )

    expected_pairs_org1 = [
        (licence_number1, registration_number1),
        (licence_number1, weca_registration_number1),
        (licence_number2, registration_number2),
        (licence_number2, registration_number6),
        (licence_number2, registration_number3),
        (licence_number2, weca_registration_number2),
        (licence_number2, weca_registration_number6),
        (licence_number2, weca_registration_number3),
    ]

    service_codes_csv = ComplianceReportCSV(org1.id)
    queryset = service_codes_csv.get_queryset()

    assert len(queryset) == len(expected_pairs_org1)
    queryset_pairs = [
        (service["otc_licence_number"], service["otc_registration_number"])
        for service in queryset
    ]
    assert sorted(queryset_pairs) == sorted(expected_pairs_org1)


@freeze_time("2023-02-24")
def test_csv_output_columns_order():
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org1 = OrganisationFactory()
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)
    services = []
    # Require Attention: No
    # TXCFileAttribute = None
    # SeasonalService = Not None and Out of Season
    services.append(
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
    services.append(
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
    services.append(
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
    txc_file_3 = TXCFileAttributesFactory(
        revision=dataset3.live_revision,
        service_code=service_codes[3],
        licence_number=otc_lic.number,
        filename="test3.xml",
        operating_period_end_date=datetime.datetime(2023, 2, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[3]],
    )

    # staleness_otc = True => "Stale - OTC Variation"
    services.append(
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
    txc_file_4 = TXCFileAttributesFactory(
        revision=dataset4.live_revision,
        service_code=service_codes[4],
        licence_number=otc_lic.number,
        filename="test4.xml",
        operating_period_end_date=datetime.datetime(2023, 3, 24),
        modification_datetime=datetime.datetime(2023, 1, 24),
        line_names=[service_numbers[4]],
    )
    # staleness_42_day_look_ahead = True => "Stale - 42 day look ahead"
    services.append(
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
    txc_file_5 = TXCFileAttributesFactory(
        revision=dataset5.live_revision,
        service_code=service_codes[5],
        licence_number=otc_lic.number,
        filename="test5.xml",
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[5]],
    )
    services.append(
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
    txc_file_6 = TXCFileAttributesFactory(
        revision=dataset6.live_revision,
        service_code=service_codes[6],
        licence_number=otc_lic.number,
        filename="test6.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[6]],
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
    services.append(
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
    txc_file_7 = TXCFileAttributesFactory(
        revision=dataset7.live_revision,
        service_code=service_codes[7],
        licence_number=otc_lic.number,
        filename="test7.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[7]],
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
    services.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[7],
            service_number=service_numbers[7],
            effective_date=datetime.datetime(2021, 1, 24),
        )
    )
    # don't care start end
    seasonal_service_7 = SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[7][-1:],
    )
    date_seasonal_service_published_7 = seasonal_service_7.start - timedelta(days=42)
    # exemption exists
    ServiceCodeExemptionFactory(
        licence=bods_licence,
        registration_code=service_codes[7][-1:],
    )

    dataset8 = DatasetFactory(organisation=org1)
    # operating_period_end_date is None
    txc_file_8 = TXCFileAttributesFactory(
        revision=dataset8.live_revision,
        service_code=service_codes[8],
        licence_number=otc_lic.number,
        filename="test8.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2023, 2, 24),
        line_names=[service_numbers[8]],
    )
    # staleness_otc = False, staleness_42_day_look_ahead = False,
    # staleness_12_months_old = False => Up to Date
    services.append(
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[8],
            service_number=service_numbers[8],
            effective_date=datetime.datetime(2021, 1, 24),
        )
    )
    seasonal_service_8 = SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[8][-1:],
    )
    date_seasonal_service_published_8 = seasonal_service_8.start - timedelta(days=42)
    # Testing something that IS in BODS but not in OTC
    licence_number = "PD0000055"

    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset9 = DatasetFactory(organisation=org1)
    txc_file_9 = TXCFileAttributesFactory(
        revision=dataset9.live_revision,
        licence_number=bods_licence.number,
        operating_period_end_date=None,
        filename="test9.xml",
        service_code="Z10",
        modification_datetime=datetime.datetime(2023, 2, 24),
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    service_codes_csv = ComplianceReportCSV(org1.id)
    csv_string = service_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)
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
    assert actual_columns[13] == "Error in AVL to Timetable Matching"
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
@override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
def test_csv_output():
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]
    national_operator_codes = ["BLAC", "LNUD"]
    operator_factory = OperatorModelFactory(operator_name="operator")
    org1 = OrganisationFactory(name="test_org_1", nocs=national_operator_codes)
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)
    services = []

    dataset1 = DatasetFactory(organisation=org1)
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
    services.append(service_1)
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2024, 2, 24),
        end=datetime.datetime(2026, 2, 24),
    )

    dataset2 = DatasetFactory(organisation=org1)
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
    services.append(service_2)
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[1][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )

    dataset3 = DatasetFactory(organisation=org1)
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
    services.append(service_3)
    ServiceCodeExemptionFactory(
        licence=bods_licence,
        registration_code=service_codes[2][-1:],
    )

    dataset4 = DatasetFactory(organisation=org1)
    # Require Attention: Yes
    # operating_period_end_date is not None
    txc_file_4 = TXCFileAttributesFactory(
        revision=dataset4.live_revision,
        service_code=service_codes[3],
        licence_number=otc_lic.number,
        filename="test3.xml",
        operating_period_end_date=datetime.datetime(2023, 2, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[3]],
        national_operator_code=national_operator_codes[0],
    )

    # staleness_otc = True => "Stale - OTC Variation"
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
    services.append(service_4)
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[3][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )
    fares_dataset4 = DatasetFactory(organisation=org1, dataset_type=FaresType)
    fares_revision4 = FaresDatasetRevisionFactory(
        dataset__organisation=org1,
        dataset__live_revision=fares_dataset4.id,
    )
    faresmetadata4 = FaresMetadataFactory(
        revision=fares_revision4,
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
    )
    faresdatacatalogue4 = DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata4,
        fares_metadata__revision__is_published=True,
        line_name=[f":::{service_numbers[3]}"],
        line_id=[f":::{service_numbers[3]}"],
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
        national_operator_code=[national_operator_codes[0]],
    )
    FaresValidationResultFactory(
        revision=fares_revision4,
        organisation=org1,
        count=0,
    )
    last_updated_date_4 = fares_revision4.published_at.date()
    fares_data_over_one_year_4 = last_updated_date_4 + timedelta(days=365)
    valid_to_4 = faresmetadata4.valid_to.date()

    dataset5 = DatasetFactory(organisation=org1)
    # Require Attention: Yes
    # operating_period_end_date is not None
    txc_file_5 = TXCFileAttributesFactory(
        revision=dataset5.live_revision,
        service_code=service_codes[4],
        licence_number=otc_lic.number,
        filename="test4.xml",
        operating_period_end_date=datetime.datetime(2023, 3, 24),
        modification_datetime=datetime.datetime(2023, 1, 24),
        line_names=[service_numbers[4]],
        national_operator_code=national_operator_codes[0],
    )
    # staleness_42_day_look_ahead = True => "Stale - 42 day look ahead"
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
    services.append(service_5)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[4][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )
    fares_dataset5 = DatasetFactory(organisation=org1, dataset_type=FaresType)
    fares_revision5 = FaresDatasetRevisionFactory(
        dataset__organisation=org1,
        dataset__live_revision=fares_dataset5.id,
    )
    faresmetadata5 = FaresMetadataFactory(
        revision=fares_revision5,
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
    )
    faresdatacatalogue5 = DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata5,
        fares_metadata__revision__is_published=True,
        line_name=[f":::{service_numbers[4]}"],
        line_id=[f":::{service_numbers[4]}"],
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
        national_operator_code=[national_operator_codes[0]],
    )
    FaresValidationResultFactory(
        revision=fares_revision5,
        organisation=org1,
        count=5,
    )
    last_updated_date_5 = fares_revision5.published_at.date()
    fares_data_over_one_year_5 = last_updated_date_5 + timedelta(days=365)
    valid_to_5 = faresmetadata5.valid_to.date()

    dataset6 = DatasetFactory(organisation=org1)
    # operating_period_end_date is not None
    txc_file_6 = TXCFileAttributesFactory(
        revision=dataset6.live_revision,
        service_code=service_codes[5],
        licence_number=otc_lic.number,
        filename="test5.xml",
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[5]],
        national_operator_code=national_operator_codes[0],
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
    services.append(service_6)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[5][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )
    fares_dataset6 = DatasetFactory(organisation=org1, dataset_type=FaresType)
    fares_revision6 = FaresDatasetRevisionFactory(
        dataset__organisation=org1,
        dataset__live_revision=fares_dataset6.id,
    )
    faresmetadata6 = FaresMetadataFactory(
        revision=fares_revision6,
        valid_from=datetime.datetime(2022, 12, 12),
        valid_to=datetime.datetime(2023, 1, 2),
    )
    faresdatacatalogue6 = DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata6,
        fares_metadata__revision__is_published=True,
        line_name=[f":::{service_numbers[5]}"],
        line_id=[f":::{service_numbers[5]}"],
        valid_from=datetime.datetime(2022, 12, 12),
        valid_to=datetime.datetime(2023, 1, 2),
        national_operator_code=[national_operator_codes[0]],
    )
    FaresValidationResultFactory(
        revision=fares_revision6,
        organisation=org1,
        count=5,
    )
    last_updated_date_6 = fares_revision6.published_at.date()
    fares_data_over_one_year_6 = last_updated_date_6 + timedelta(days=365)
    valid_to_6 = faresmetadata6.valid_to.date()

    dataset7 = DatasetFactory(organisation=org1)
    # operating_period_end_date is None
    txc_file_7 = TXCFileAttributesFactory(
        revision=dataset7.live_revision,
        service_code=service_codes[6],
        licence_number=otc_lic.number,
        filename="test6.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[6]],
        national_operator_code=national_operator_codes[0],
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
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
    services.append(service_7)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[6][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )
    fares_dataset7 = DatasetFactory(organisation=org1, dataset_type=FaresType)
    fares_revision7 = FaresDatasetRevisionFactory(
        dataset__organisation=org1,
        dataset__live_revision=fares_dataset7.id,
        published_at=datetime.datetime(2022, 1, 1),
    )
    faresmetadata7 = FaresMetadataFactory(
        revision=fares_revision7,
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
    )
    faresdatacatalogue7 = DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata7,
        fares_metadata__revision__is_published=True,
        line_name=[f":::{service_numbers[6]}"],
        line_id=[f":::{service_numbers[6]}"],
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
        national_operator_code=[national_operator_codes[0]],
    )
    FaresValidationResultFactory(
        revision=fares_revision7,
        organisation=org1,
        count=5,
    )
    last_updated_date_7 = fares_revision7.published_at.date()
    fares_data_over_one_year_7 = last_updated_date_7 + timedelta(days=365)
    valid_to_7 = faresmetadata7.valid_to.date()

    dataset8 = DatasetFactory(organisation=org1)
    # Require Attention: No
    # operating_period_end_date is None
    txc_file_8 = TXCFileAttributesFactory(
        revision=dataset8.live_revision,
        service_code=service_codes[7],
        licence_number=otc_lic.number,
        filename="test7.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[7]],
        national_operator_code=national_operator_codes[0],
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
    service_8 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[7],
        service_number=service_numbers[7],
        effective_date=datetime.datetime(2021, 1, 24),
        variation_number=88,
        start_point="start point service 8",
        finish_point="finish point service 8",
        via="via service 8",
        service_type_other_details="service type detail service 8",
        description="description service 8",
        operator=operator_factory,
        service_type_description="service type description service 8",
    )
    services.append(service_8)
    seasonal_service_8 = SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[7][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )
    date_seasonal_service_published_8 = seasonal_service_8.start - timedelta(days=42)
    # exemption exists
    ServiceCodeExemptionFactory(
        licence=bods_licence,
        registration_code=service_codes[7][-1:],
    )
    fares_dataset8 = DatasetFactory(organisation=org1, dataset_type=FaresType)
    fares_revision8 = FaresDatasetRevisionFactory(
        dataset__organisation=org1,
        dataset__live_revision=fares_dataset8.id,
        published_at=datetime.datetime(2022, 1, 1),
    )
    faresmetadata8 = FaresMetadataFactory(
        revision=fares_revision8,
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
    )
    faresdatacatalogue8 = DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata8,
        fares_metadata__revision__is_published=True,
        line_name=[f":::{service_numbers[7]}"],
        line_id=[f":::{service_numbers[7]}"],
        valid_from=datetime.datetime(2024, 12, 12),
        valid_to=datetime.datetime(2025, 1, 12),
        national_operator_code=[national_operator_codes[0]],
    )
    FaresValidationResultFactory(
        revision=fares_revision8,
        organisation=org1,
        count=0,
    )
    last_updated_date_8 = fares_revision8.published_at.date()
    fares_data_over_one_year_8 = last_updated_date_8 + timedelta(days=365)
    valid_to_8 = faresmetadata8.valid_to.date()

    dataset9 = DatasetFactory(organisation=org1)
    # operating_period_end_date is None
    txc_file_9 = TXCFileAttributesFactory(
        revision=dataset8.live_revision,
        service_code=service_codes[8],
        licence_number=otc_lic.number,
        filename="test8.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2023, 2, 24),
        line_names=[service_numbers[8]],
        national_operator_code=national_operator_codes[0],
    )
    # staleness_otc = False, staleness_42_day_look_ahead = False,
    # staleness_12_months_old = False => Up to Date
    service_9 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[8],
        service_number=service_numbers[8],
        effective_date=datetime.datetime(2021, 1, 24),
        variation_number=99,
        start_point="start point service 9",
        finish_point="finish point service 9",
        via="via service 9",
        service_type_other_details="service type detail service 9",
        description="description service 9",
        operator=operator_factory,
        service_type_description="service type description service 9",
    )
    services.append(service_9)
    seasonal_service_9 = SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[8][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2024, 2, 24),
    )
    date_seasonal_service_published_9 = seasonal_service_9.start - timedelta(days=42)
    fares_dataset9 = DatasetFactory(organisation=org1, dataset_type=FaresType)
    fares_revision9 = FaresDatasetRevisionFactory(
        dataset__organisation=org1,
        dataset__live_revision=fares_dataset9.id,
    )
    faresmetadata9 = FaresMetadataFactory(
        revision=fares_revision9,
        valid_from=datetime.datetime(2022, 12, 12),
        valid_to=datetime.datetime(2023, 1, 2),
    )
    faresdatacatalogue9 = DataCatalogueMetaDataFactory(
        fares_metadata=faresmetadata9,
        fares_metadata__revision__is_published=True,
        line_name=[f":::{service_numbers[8]}"],
        line_id=[f":::{service_numbers[8]}"],
        valid_from=datetime.datetime(2022, 12, 12),
        valid_to=datetime.datetime(2023, 1, 2),
        national_operator_code=[national_operator_codes[0]],
    )
    FaresValidationResultFactory(
        revision=fares_revision9,
        organisation=org1,
        count=0,
    )
    last_updated_date_9 = fares_revision9.published_at.date()
    fares_data_over_one_year_9 = last_updated_date_9 + timedelta(days=365)
    valid_to_9 = faresmetadata9.valid_to.date()

    # Testing something that IS in BODS but not in OTC
    licence_number = "PD0000055"

    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset10 = DatasetFactory(organisation=org1)
    txc_file_10 = TXCFileAttributesFactory(
        revision=dataset9.live_revision,
        licence_number=bods_licence.number,
        operating_period_end_date=None,
        filename="test9.xml",
        service_code="Z10",
        modification_datetime=datetime.datetime(2023, 2, 24),
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2022, 2, 24),
        end=datetime.datetime(2022, 2, 24),
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    service_codes_csv = ComplianceReportCSV(org1.id)
    csv_string = service_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    assert csv_output["row0"][0] == '"PD0000099:0"'  # Registration:Registration Number
    assert csv_output["row0"][1] == '"Line0"'  # Registration:Service Number
    assert csv_output["row0"][2] == '"Registered"'  # Registration Status
    assert csv_output["row0"][3] == '"In Scope"'  # Scope Status
    assert csv_output["row0"][4] == '"Out of Season"'  # Seasonal Status
    assert csv_output["row0"][5] == '"test_org_1"'  # Organisation Name
    assert csv_output["row0"][6] == '"No"'  # Requires Attention
    assert csv_output["row0"][7] == '"No"'  # Timetables requires attention
    assert csv_output["row0"][8] == '"Unpublished"'  # Timetables Published Status
    assert csv_output["row0"][9] == '"Up to date"'  # Timetables Timeliness Status
    assert (
        csv_output["row0"][10] == '"Under maintenance"'
    )  # Timetables critical DQ issues
    assert csv_output["row0"][11] == '"Yes"'  # AVL requires attention
    assert csv_output["row0"][12] == '"No"'  # AVL Published Status
    assert csv_output["row0"][13] == '"No"'  # Error in AVL to Timetable Matching
    assert csv_output["row0"][14] == '"Yes"'  # Fares requires attention
    assert csv_output["row0"][15] == '"Unpublished"'  # Fares Published Status
    assert csv_output["row0"][16] == '"Not Stale"'  # Fares Timeliness Status
    assert csv_output["row0"][17] == '"No"'  # Fares Compliance Status
    assert csv_output["row0"][18] == '""'  # Timetables Data set ID
    assert csv_output["row0"][19] == '""'  # TXC:Filename
    assert csv_output["row0"][20] == '""'  # TXC:NOC
    assert csv_output["row0"][21] == '""'  # TXC:Last Modified Date
    assert csv_output["row0"][22] == '""'  # Date when timetable data is over 1 year old
    assert csv_output["row0"][23] == '""'  # TXC:Operating Period End Date
    assert csv_output["row0"][24] == '""'  # Fares Data set ID
    assert csv_output["row0"][25] == '""'  # NETEX:Filename
    assert csv_output["row0"][26] == '""'  # NETEX:Last Modified Date
    assert csv_output["row0"][27] == '""'  # Date when fares data is over 1 year old
    assert csv_output["row0"][28] == '""'  # NETEX:Operating Period End Date
    assert (
        csv_output["row0"][29] == '"2023-05-12"'
    )  # Date Registration variation needs to be published
    assert (
        csv_output["row0"][30] == '"2023-04-07"'
    )  # Date for complete 42 day look ahead
    assert (
        csv_output["row0"][31] == '"2024-01-13"'
    )  # Date seasonal service should be published"
    assert csv_output["row0"][32] == '"2024-02-24"'  # Seasonal Start dDate
    assert csv_output["row0"][33] == '"2026-02-24"'  # Seasonal End Date
    assert csv_output["row0"][34] == '"operator"'  # Registration:Operator Name
    assert csv_output["row0"][35] == '"PD0000099"'  # Registration:Licence Number
    assert (
        csv_output["row0"][36] == '"service type description service 1"'
    )  # Registration:Service Type Description
    assert csv_output["row0"][37] == '"11"'  # Registration:Variation Number
    assert (
        csv_output["row0"][38] == f'"{otc_lic.expiry_date}"'
    )  # Registration:Expiry Date
    assert csv_output["row0"][39] == '"2023-06-24"'  # Registration:Effective Date
    assert (
        csv_output["row0"][40] == f'"{service_1.received_date}"'
    )  # Registration:Received Date
    assert csv_output["row0"][41] == '"South East"'  # Traveline Region
    assert csv_output["row0"][42] == '"UI_LTA"'  # Local Transport Authority

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
    assert csv_output["row1"][14] == '"Yes"'
    assert csv_output["row1"][15] == '"Unpublished"'
    assert csv_output["row1"][16] == '"Not Stale"'
    assert csv_output["row1"][17] == '"No"'
    assert csv_output["row1"][18] == '""'
    assert csv_output["row1"][19] == '""'
    assert csv_output["row1"][20] == '""'
    assert csv_output["row1"][21] == '""'
    assert csv_output["row1"][22] == '""'
    assert csv_output["row1"][23] == '""'
    assert csv_output["row1"][24] == '""'
    assert csv_output["row1"][25] == '""'
    assert csv_output["row1"][26] == '""'
    assert csv_output["row1"][27] == '""'
    assert csv_output["row1"][28] == '""'
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
    assert csv_output["row2"][14] == '"Yes"'
    assert csv_output["row2"][15] == '"Unpublished"'
    assert csv_output["row2"][16] == '"Not Stale"'
    assert csv_output["row2"][17] == '"No"'
    assert csv_output["row2"][18] == '""'
    assert csv_output["row2"][19] == '""'
    assert csv_output["row2"][20] == '""'
    assert csv_output["row2"][21] == '""'
    assert csv_output["row2"][22] == '""'
    assert csv_output["row2"][23] == '""'
    assert csv_output["row2"][24] == '""'
    assert csv_output["row2"][25] == '""'
    assert csv_output["row2"][26] == '""'
    assert csv_output["row2"][27] == '""'
    assert csv_output["row2"][28] == '""'
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
    assert csv_output["row3"][8] == '"Published"'
    assert csv_output["row3"][9] == '"OTC variation not published"'
    assert csv_output["row3"][10] == '"Under maintenance"'
    assert csv_output["row3"][11] == '"Yes"'
    assert csv_output["row3"][12] == '"No"'
    assert csv_output["row3"][13] == '"No"'
    assert csv_output["row3"][14] == '"No"'
    assert csv_output["row3"][15] == '"Published"'
    assert csv_output["row3"][16] == '"Not Stale"'
    assert csv_output["row3"][17] == '"Yes"'
    assert csv_output["row3"][18] == f'"{txc_file_4.revision.dataset_id}"'
    assert csv_output["row3"][19] == '"test3.xml"'
    assert csv_output["row3"][20] == '"BLAC"'
    assert csv_output["row3"][21] == '"2022-01-24"'
    assert csv_output["row3"][22] == '"2023-01-24"'
    assert csv_output["row3"][23] == '"2023-02-24"'
    assert csv_output["row3"][24] == f'"{fares_revision4.dataset.id}"'
    assert csv_output["row3"][25] == f'"{faresdatacatalogue4.xml_file_name}"'
    assert csv_output["row3"][26] == f'"{last_updated_date_4}"'
    assert csv_output["row3"][27] == f'"{fares_data_over_one_year_4}"'
    assert csv_output["row3"][28] == f'"{valid_to_4}"'
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
    assert csv_output["row4"][8] == '"Published"'
    assert csv_output["row4"][9] == '"42 day look ahead is incomplete"'
    assert csv_output["row4"][10] == '"Under maintenance"'
    assert csv_output["row4"][11] == '"Yes"'
    assert csv_output["row4"][12] == '"No"'
    assert csv_output["row4"][13] == '"No"'
    assert csv_output["row4"][14] == '"Yes"'
    assert csv_output["row4"][15] == '"Published"'
    assert csv_output["row4"][16] == '"Not Stale"'
    assert csv_output["row4"][17] == '"No"'
    assert csv_output["row4"][18] == f'"{txc_file_5.revision.dataset_id}"'
    assert csv_output["row4"][19] == '"test4.xml"'
    assert csv_output["row4"][20] == f'"{txc_file_5.national_operator_code}"'
    assert csv_output["row4"][21] == '"2023-01-24"'
    assert csv_output["row4"][22] == '"2024-01-24"'
    assert csv_output["row4"][23] == '"2023-03-24"'
    assert csv_output["row4"][24] == f'"{fares_revision5.dataset.id}"'
    assert csv_output["row4"][25] == f'"{faresdatacatalogue5.xml_file_name}"'
    assert csv_output["row4"][26] == f'"{last_updated_date_5}"'
    assert csv_output["row4"][27] == f'"{fares_data_over_one_year_5}"'
    assert csv_output["row4"][28] == f'"{valid_to_5}"'
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
    assert csv_output["row5"][8] == '"Published"'
    assert csv_output["row5"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row5"][10] == '"Under maintenance"'
    assert csv_output["row5"][11] == '"Yes"'
    assert csv_output["row5"][12] == '"No"'
    assert csv_output["row5"][13] == '"No"'
    assert csv_output["row5"][14] == '"Yes"'
    assert csv_output["row5"][15] == '"Published"'
    assert csv_output["row5"][16] == '"42 day look ahead is incomplete"'
    assert csv_output["row5"][17] == '"No"'
    assert csv_output["row5"][18] == f'"{txc_file_6.revision.dataset_id}"'
    assert csv_output["row5"][19] == '"test5.xml"'
    assert csv_output["row5"][20] == f'"{txc_file_6.national_operator_code}"'
    assert csv_output["row5"][21] == '"2022-01-24"'
    assert csv_output["row5"][22] == '"2023-01-24"'
    assert csv_output["row5"][23] == '"2023-06-24"'
    assert csv_output["row5"][24] == f'"{fares_revision6.dataset.id}"'
    assert csv_output["row5"][25] == f'"{faresdatacatalogue6.xml_file_name}"'
    assert csv_output["row5"][26] == f'"{last_updated_date_6}"'
    assert csv_output["row5"][27] == f'"{fares_data_over_one_year_6}"'
    assert csv_output["row5"][28] == f'"{valid_to_6}"'
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
    assert csv_output["row6"][8] == '"Published"'
    assert csv_output["row6"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row6"][10] == '"Under maintenance"'
    assert csv_output["row6"][11] == '"Yes"'
    assert csv_output["row6"][12] == '"No"'
    assert csv_output["row6"][13] == '"No"'
    assert csv_output["row6"][14] == '"Yes"'
    assert csv_output["row6"][15] == '"Published"'
    assert csv_output["row6"][16] == '"One year old"'
    assert csv_output["row6"][17] == '"No"'
    assert csv_output["row6"][18] == f'"{txc_file_7.revision.dataset_id}"'
    assert csv_output["row6"][19] == '"test6.xml"'
    assert csv_output["row6"][20] == f'"{txc_file_7.national_operator_code}"'
    assert csv_output["row6"][21] == '"2022-01-24"'
    assert csv_output["row6"][22] == '"2023-01-24"'
    assert csv_output["row6"][23] == '""'
    assert csv_output["row6"][24] == f'"{fares_revision7.dataset.id}"'
    assert csv_output["row6"][25] == f'"{faresdatacatalogue7.xml_file_name}"'
    assert csv_output["row6"][26] == f'"{last_updated_date_7}"'
    assert csv_output["row6"][27] == f'"{fares_data_over_one_year_7}"'
    assert csv_output["row6"][28] == f'"{valid_to_7}"'
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

    assert csv_output["row7"][0] == '"PD0000099:7"'
    assert csv_output["row7"][1] == '"Line7"'
    assert csv_output["row7"][2] == '"Registered"'
    assert csv_output["row7"][3] == '"Out of Scope"'
    assert csv_output["row7"][4] == '"In Season"'
    assert csv_output["row7"][5] == '"test_org_1"'
    assert csv_output["row7"][6] == '"No"'
    assert csv_output["row7"][7] == '"No"'
    assert csv_output["row7"][8] == '"Published"'
    assert csv_output["row7"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row7"][10] == '"Under maintenance"'
    assert csv_output["row7"][11] == '"Yes"'
    assert csv_output["row7"][12] == '"No"'
    assert csv_output["row7"][13] == '"No"'
    assert csv_output["row7"][14] == '"Yes"'
    assert csv_output["row7"][15] == '"Published"'
    assert csv_output["row7"][16] == '"One year old"'
    assert csv_output["row7"][17] == '"Yes"'
    assert csv_output["row7"][18] == f'"{txc_file_8.revision.dataset_id}"'
    assert csv_output["row7"][19] == '"test7.xml"'
    assert csv_output["row7"][20] == f'"{txc_file_8.national_operator_code}"'
    assert csv_output["row7"][21] == '"2022-01-24"'
    assert csv_output["row7"][22] == '"2023-01-24"'
    assert csv_output["row7"][23] == '""'
    assert csv_output["row7"][24] == f'"{fares_revision8.dataset.id}"'
    assert csv_output["row7"][25] == f'"{faresdatacatalogue8.xml_file_name}"'
    assert csv_output["row7"][26] == f'"{last_updated_date_8}"'
    assert csv_output["row7"][27] == f'"{fares_data_over_one_year_8}"'
    assert csv_output["row7"][28] == f'"{valid_to_8}"'
    assert csv_output["row7"][29] == '"2020-12-13"'
    assert csv_output["row7"][30] == '"2023-04-07"'
    assert csv_output["row7"][31] == '"2022-01-13"'
    assert csv_output["row7"][32] == '"2022-02-24"'
    assert csv_output["row7"][33] == '"2024-02-24"'
    assert csv_output["row7"][34] == '"operator"'
    assert csv_output["row7"][35] == '"PD0000099"'
    assert csv_output["row7"][36] == '"service type description service 8"'
    assert csv_output["row7"][37] == '"88"'
    assert csv_output["row7"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row7"][39] == '"2021-01-24"'
    assert csv_output["row7"][40] == f'"{service_8.received_date}"'
    assert csv_output["row7"][41] == '"South East"'
    assert csv_output["row7"][42] == '"UI_LTA"'

    assert csv_output["row8"][0] == '"PD0000099:8"'
    assert csv_output["row8"][1] == '"Line8"'
    assert csv_output["row8"][2] == '"Registered"'
    assert csv_output["row8"][3] == '"In Scope"'
    assert csv_output["row8"][4] == '"In Season"'
    assert csv_output["row8"][5] == '"test_org_1"'
    assert csv_output["row8"][6] == '"Yes"'
    assert csv_output["row8"][7] == '"No"'
    assert csv_output["row8"][8] == '"Published"'
    assert csv_output["row8"][9] == '"Up to date"'
    assert csv_output["row8"][10] == '"Under maintenance"'
    assert csv_output["row8"][11] == '"Yes"'
    assert csv_output["row8"][12] == '"No"'
    assert csv_output["row8"][13] == '"No"'
    assert csv_output["row8"][14] == '"Yes"'
    assert csv_output["row8"][15] == '"Published"'
    assert csv_output["row8"][16] == '"42 day look ahead is incomplete"'
    assert csv_output["row8"][17] == '"Yes"'
    assert csv_output["row8"][18] == f'"{txc_file_9.revision.dataset_id}"'
    assert csv_output["row8"][19] == '"test8.xml"'
    assert csv_output["row8"][20] == f'"{txc_file_9.national_operator_code}"'
    assert csv_output["row8"][21] == '"2023-02-24"'
    assert csv_output["row8"][22] == '"2024-02-24"'
    assert csv_output["row8"][23] == '""'
    assert csv_output["row8"][24] == f'"{fares_revision9.dataset.id}"'
    assert csv_output["row8"][25] == f'"{faresdatacatalogue9.xml_file_name}"'
    assert csv_output["row8"][26] == f'"{last_updated_date_9}"'
    assert csv_output["row8"][27] == f'"{fares_data_over_one_year_9}"'
    assert csv_output["row8"][28] == f'"{valid_to_9}"'
    assert csv_output["row8"][29] == '"2020-12-13"'
    assert csv_output["row8"][30] == '"2023-04-07"'
    assert csv_output["row8"][31] == '"2022-01-13"'
    assert csv_output["row8"][32] == '"2022-02-24"'
    assert csv_output["row8"][33] == '"2024-02-24"'
    assert csv_output["row8"][34] == '"operator"'
    assert csv_output["row8"][35] == '"PD0000099"'
    assert csv_output["row8"][36] == '"service type description service 9"'
    assert csv_output["row8"][37] == '"99"'
    assert csv_output["row8"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row8"][39] == '"2021-01-24"'
    assert csv_output["row8"][40] == f'"{service_9.received_date}"'
    assert csv_output["row8"][41] == '"South East"'
    assert csv_output["row8"][42] == '"UI_LTA"'

    # unregistered service i.e. row 9 will be missing,
    assert ("row9" not in csv_output) == True


@freeze_time("2023-02-28")
@override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
def test_weca_seasonal_status_csv_output():
    """Test Operator report for weca season services
    Match the CSV row outputs
    """
    licence_number = "PD0001111"
    num_otc_services = 10
    service_code_prefix = "1101000"
    service_codes = [
        f"{licence_number}:{service_code_prefix}{n}" for n in range(num_otc_services)
    ]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    atco_code = "110"
    registration_code_index = -len(service_code_prefix) - 1
    operator_factory = OperatorModelFactory(operator_name="operator")
    org = OrganisationFactory(name="test_org_1")
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)

    services = []

    # Up to Date
    dataset0 = DatasetFactory(organisation=org)
    txc_file_0 = TXCFileAttributesFactory(
        revision=dataset0.live_revision,
        service_code=service_codes[0],
        operating_period_end_date=datetime.datetime(2023, 6, 28),
        modification_datetime=datetime.datetime(2022, 1, 28),
        line_names=[service_numbers[0]],
        filename="test0.xml",
    )
    service_0 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[0],
        service_number=service_numbers[0],
        effective_date=datetime.datetime(2024, 1, 28),
        api_type=API_TYPE_WECA,
        atco_code=atco_code,
        variation_number=0,
        start_point="start point service 0",
        finish_point="finish point service 0",
        via="via service 0",
        service_type_other_details="service type detail service 0",
        description="description service 0",
        operator=operator_factory,
        service_type_description="service type description service 0",
    )
    services.append(service_0)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][registration_code_index:],
        start=datetime.datetime(2022, 2, 28),
        end=datetime.datetime(2024, 2, 28),
    )

    dataset1 = DatasetFactory(organisation=org)
    txc_file_1 = TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=service_codes[1],
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[1]],
        filename="test1.xml",
    )
    service_1 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[1],
        service_number=service_numbers[1],
        effective_date=datetime.datetime(2024, 1, 24),
        api_type=API_TYPE_WECA,
        atco_code=atco_code,
        variation_number=1,
        start_point="start point service 1",
        finish_point="finish point service 1",
        via="via service 1",
        service_type_other_details="service type detail service 1",
        description="description service 1",
        operator=operator_factory,
        service_type_description="service type description service 1",
    )
    services.append(service_1)
    # out of season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[1][registration_code_index:],
        start=datetime.datetime(2026, 2, 28),
        end=datetime.datetime(2028, 2, 28),
    )

    # Not Seasonal
    dataset2 = DatasetFactory(organisation=org)
    txc_file_2 = TXCFileAttributesFactory(
        revision=dataset2.live_revision,
        service_code=service_codes[2],
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[2]],
        filename="test2.xml",
    )
    service_2 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[2],
        service_number=service_numbers[2],
        effective_date=datetime.datetime(2024, 1, 24),
        api_type=API_TYPE_WECA,
        atco_code=atco_code,
        variation_number=2,
        start_point="start point service 2",
        finish_point="finish point service 2",
        via="via service 2",
        service_type_other_details="service type detail service 2",
        description="description service 2",
        operator=operator_factory,
        service_type_description="service type description service 2",
    )
    services.append(service_2)

    dataset3 = DatasetFactory(organisation=org)
    # operating_period_end_date is None
    txc_file_3 = TXCFileAttributesFactory(
        revision=dataset3.live_revision,
        service_code=service_codes[3],
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 28),
        line_names=[service_numbers[3]],
        filename="test3.xml",
    )
    # is_stale: staleness_12_months_old = True => "Stale - 12 months old"
    service_3 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[3],
        service_number=service_numbers[3],
        effective_date=datetime.datetime(2021, 1, 28),
        api_type=API_TYPE_WECA,
        atco_code=atco_code,
        variation_number=3,
        start_point="start point service 3",
        finish_point="finish point service 3",
        via="via service 3",
        service_type_other_details="service type detail service 3",
        description="description service 3",
        operator=operator_factory,
        service_type_description="service type description service 3",
    )
    services.append(service_3)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[3][registration_code_index:],
        start=datetime.datetime(2022, 2, 28),
        end=datetime.datetime(2024, 2, 28),
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

    service_codes_csv = ComplianceReportCSV(org.id)
    csv_string = service_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    assert csv_output["row0"][0] == f'"PD0001111:{service_code_prefix}0"'
    assert csv_output["row0"][1] == '"Line0"'
    assert csv_output["row0"][2] == '"Registered"'
    assert csv_output["row0"][3] == '"In Scope"'
    assert csv_output["row0"][4] == '"In Season"'
    assert csv_output["row0"][5] == '"test_org_1"'
    assert csv_output["row0"][6] == '"Yes"'
    assert csv_output["row0"][7] == '"Yes"'
    assert csv_output["row0"][8] == '"Published"'
    assert csv_output["row0"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row0"][10] == '"Under maintenance"'
    assert csv_output["row0"][11] == '"Yes"'
    assert csv_output["row0"][12] == '"No"'
    assert csv_output["row0"][13] == '"No"'
    assert csv_output["row0"][14] == '"Yes"'
    assert csv_output["row0"][15] == '"Unpublished"'
    assert csv_output["row0"][16] == '"Not Stale"'
    assert csv_output["row0"][17] == '"No"'
    assert csv_output["row0"][18] == f'"{dataset0.id}"'
    assert csv_output["row0"][19] == '"test0.xml"'
    assert csv_output["row0"][20] == f'"{txc_file_0.national_operator_code}"'
    assert csv_output["row0"][21] == '"2022-01-28"'
    assert csv_output["row0"][22] == '"2023-01-28"'
    assert csv_output["row0"][23] == '"2023-06-28"'
    assert csv_output["row0"][24] == '""'
    assert csv_output["row0"][25] == '""'
    assert csv_output["row0"][26] == '""'
    assert csv_output["row0"][27] == '""'
    assert csv_output["row0"][28] == '""'
    assert csv_output["row0"][29] == '"2023-12-17"'
    assert csv_output["row0"][30] == '"2023-04-11"'
    assert csv_output["row0"][31] == '"2022-01-17"'
    assert csv_output["row0"][32] == '"2022-02-28"'
    assert csv_output["row0"][33] == '"2024-02-28"'
    assert csv_output["row0"][34] == '"operator"'
    assert csv_output["row0"][35] == '"PD0001111"'
    assert csv_output["row0"][36] == '"service type description service 0"'
    assert csv_output["row0"][37] == '"0"'
    assert csv_output["row0"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row0"][39] == '"2024-01-28"'
    assert csv_output["row0"][40] == f'"{service_0.received_date}"'
    assert csv_output["row0"][41] == '"South East"'
    assert csv_output["row0"][42] == '"UI_LTA"'

    assert csv_output["row1"][0] == f'"PD0001111:{service_code_prefix}1"'
    assert csv_output["row1"][1] == '"Line1"'
    assert csv_output["row1"][2] == '"Registered"'
    assert csv_output["row1"][3] == '"In Scope"'
    assert csv_output["row1"][4] == '"Out of Season"'
    assert csv_output["row1"][5] == '"test_org_1"'
    assert csv_output["row1"][6] == '"No"'
    assert csv_output["row1"][7] == '"No"'
    assert csv_output["row1"][8] == '"Published"'
    assert csv_output["row1"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row1"][10] == '"Under maintenance"'
    assert csv_output["row1"][11] == '"Yes"'
    assert csv_output["row1"][12] == '"No"'
    assert csv_output["row1"][13] == '"No"'
    assert csv_output["row1"][14] == '"Yes"'
    assert csv_output["row1"][15] == '"Unpublished"'
    assert csv_output["row1"][16] == '"Not Stale"'
    assert csv_output["row1"][17] == '"No"'
    assert csv_output["row1"][18] == f'"{dataset1.id}"'
    assert csv_output["row1"][19] == '"test1.xml"'
    assert csv_output["row1"][20] == f'"{txc_file_1.national_operator_code}"'
    assert csv_output["row1"][21] == '"2022-01-24"'
    assert csv_output["row1"][22] == '"2023-01-24"'
    assert csv_output["row1"][23] == '"2023-06-24"'
    assert csv_output["row1"][24] == '""'
    assert csv_output["row1"][25] == '""'
    assert csv_output["row1"][26] == '""'
    assert csv_output["row1"][27] == '""'
    assert csv_output["row1"][28] == '""'
    assert csv_output["row1"][29] == '"2023-12-13"'
    assert csv_output["row1"][30] == '"2023-04-11"'
    assert csv_output["row1"][31] == '"2026-01-17"'
    assert csv_output["row1"][32] == '"2026-02-28"'
    assert csv_output["row1"][33] == '"2028-02-28"'
    assert csv_output["row1"][34] == '"operator"'
    assert csv_output["row1"][35] == '"PD0001111"'
    assert csv_output["row1"][36] == '"service type description service 1"'
    assert csv_output["row1"][37] == '"1"'
    assert csv_output["row1"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row1"][39] == '"2024-01-24"'
    assert csv_output["row1"][40] == f'"{service_1.received_date}"'
    assert csv_output["row1"][41] == '"South East"'
    assert csv_output["row1"][42] == '"UI_LTA"'

    assert csv_output["row2"][0] == f'"PD0001111:{service_code_prefix}2"'
    assert csv_output["row2"][1] == '"Line2"'
    assert csv_output["row2"][2] == '"Registered"'
    assert csv_output["row2"][3] == '"In Scope"'
    assert csv_output["row2"][4] == '"Not Seasonal"'
    assert csv_output["row2"][5] == '"test_org_1"'
    assert csv_output["row2"][6] == '"Yes"'
    assert csv_output["row2"][7] == '"Yes"'
    assert csv_output["row2"][8] == '"Published"'
    assert csv_output["row2"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row2"][10] == '"Under maintenance"'
    assert csv_output["row2"][11] == '"Yes"'
    assert csv_output["row2"][12] == '"No"'
    assert csv_output["row2"][13] == '"No"'
    assert csv_output["row2"][14] == '"Yes"'
    assert csv_output["row2"][15] == '"Unpublished"'
    assert csv_output["row2"][16] == '"Not Stale"'
    assert csv_output["row2"][17] == '"No"'
    assert csv_output["row2"][18] == f'"{dataset2.id}"'
    assert csv_output["row2"][19] == '"test2.xml"'
    assert csv_output["row2"][20] == f'"{txc_file_2.national_operator_code}"'
    assert csv_output["row2"][21] == '"2022-01-24"'
    assert csv_output["row2"][22] == '"2023-01-24"'
    assert csv_output["row2"][23] == '"2023-06-24"'
    assert csv_output["row2"][24] == '""'
    assert csv_output["row2"][25] == '""'
    assert csv_output["row2"][26] == '""'
    assert csv_output["row2"][27] == '""'
    assert csv_output["row2"][28] == '""'
    assert csv_output["row2"][29] == '"2023-12-13"'
    assert csv_output["row2"][30] == '"2023-04-11"'
    assert csv_output["row2"][31] == '""'
    assert csv_output["row2"][32] == '""'
    assert csv_output["row2"][33] == '""'
    assert csv_output["row2"][34] == '"operator"'
    assert csv_output["row2"][35] == '"PD0001111"'
    assert csv_output["row2"][36] == '"service type description service 2"'
    assert csv_output["row2"][37] == '"2"'
    assert csv_output["row2"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row2"][39] == '"2024-01-24"'
    assert csv_output["row2"][40] == f'"{service_2.received_date}"'
    assert csv_output["row2"][41] == '"South East"'
    assert csv_output["row2"][42] == '"UI_LTA"'

    assert csv_output["row3"][0] == f'"PD0001111:{service_code_prefix}3"'
    assert csv_output["row3"][1] == '"Line3"'
    assert csv_output["row3"][2] == '"Registered"'
    assert csv_output["row3"][3] == '"In Scope"'
    assert csv_output["row3"][4] == '"In Season"'
    assert csv_output["row3"][5] == '"test_org_1"'
    assert csv_output["row3"][6] == '"Yes"'
    assert csv_output["row3"][7] == '"Yes"'
    assert csv_output["row3"][8] == '"Published"'
    assert csv_output["row3"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row3"][10] == '"Under maintenance"'
    assert csv_output["row3"][11] == '"Yes"'
    assert csv_output["row3"][12] == '"No"'
    assert csv_output["row3"][13] == '"No"'
    assert csv_output["row3"][14] == '"Yes"'
    assert csv_output["row3"][15] == '"Unpublished"'
    assert csv_output["row3"][16] == '"Not Stale"'
    assert csv_output["row3"][17] == '"No"'
    assert csv_output["row3"][18] == f'"{dataset3.id}"'
    assert csv_output["row3"][19] == '"test3.xml"'
    assert csv_output["row3"][20] == f'"{txc_file_3.national_operator_code}"'
    assert csv_output["row3"][21] == '"2022-01-28"'
    assert csv_output["row3"][22] == '"2023-01-28"'
    assert csv_output["row3"][23] == '""'
    assert csv_output["row3"][24] == '""'
    assert csv_output["row3"][25] == '""'
    assert csv_output["row3"][26] == '""'
    assert csv_output["row3"][27] == '""'
    assert csv_output["row3"][28] == '""'
    assert csv_output["row3"][29] == '"2020-12-17"'
    assert csv_output["row3"][30] == '"2023-04-11"'
    assert csv_output["row3"][31] == '"2022-01-17"'
    assert csv_output["row3"][32] == '"2022-02-28"'
    assert csv_output["row3"][33] == '"2024-02-28"'
    assert csv_output["row3"][34] == '"operator"'
    assert csv_output["row3"][35] == '"PD0001111"'
    assert csv_output["row3"][36] == '"service type description service 3"'
    assert csv_output["row3"][37] == '"3"'
    assert csv_output["row3"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row3"][39] == '"2021-01-28"'
    assert csv_output["row3"][40] == f'"{service_3.received_date}"'
    assert csv_output["row3"][41] == '"South East"'
    assert csv_output["row3"][42] == '"UI_LTA"'


@freeze_time("2023-02-28")
@override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
def test_seasonal_status_csv_output():
    licence_number = "PD0001111"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]
    operator_factory = OperatorModelFactory(operator_name="operator")
    org = OrganisationFactory(name="test_org_1")
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)

    services = []

    # Up to Date
    dataset0 = DatasetFactory(organisation=org)
    txc_file_0 = TXCFileAttributesFactory(
        revision=dataset0.live_revision,
        service_code=service_codes[0],
        operating_period_end_date=datetime.datetime(2023, 6, 28),
        modification_datetime=datetime.datetime(2022, 1, 28),
        line_names=[service_numbers[0]],
        filename="test0.xml",
    )
    service_0 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[0],
        service_number=service_numbers[0],
        effective_date=datetime.datetime(2024, 1, 28),
        variation_number=0,
        start_point="start point service 0",
        finish_point="finish point service 0",
        via="via service 0",
        service_type_other_details="service type detail service 0",
        description="description service 0",
        operator=operator_factory,
        service_type_description="service type description service 0",
    )
    services.append(service_0)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[0][-1:],
        start=datetime.datetime(2022, 2, 28),
        end=datetime.datetime(2024, 2, 28),
    )

    dataset1 = DatasetFactory(organisation=org)
    txc_file_1 = TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=service_codes[1],
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[1]],
        filename="test1.xml",
    )
    service_1 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[1],
        service_number=service_numbers[1],
        effective_date=datetime.datetime(2024, 1, 24),
        variation_number=1,
        start_point="start point service 1",
        finish_point="finish point service 1",
        via="via service 1",
        service_type_other_details="service type detail service 1",
        description="description service 1",
        operator=operator_factory,
        service_type_description="service type description service 1",
    )
    services.append(service_1)
    # out of season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[1][-1:],
        start=datetime.datetime(2026, 2, 28),
        end=datetime.datetime(2028, 2, 28),
    )

    # Not Seasonal
    dataset2 = DatasetFactory(organisation=org)
    txc_file_2 = TXCFileAttributesFactory(
        revision=dataset2.live_revision,
        service_code=service_codes[2],
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
        line_names=[service_numbers[2]],
        filename="test2.xml",
    )
    service_2 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[2],
        service_number=service_numbers[2],
        effective_date=datetime.datetime(2024, 1, 24),
        variation_number=2,
        start_point="start point service 2",
        finish_point="finish point service 2",
        via="via service 2",
        service_type_other_details="service type detail service 2",
        description="description service 2",
        operator=operator_factory,
        service_type_description="service type description service 2",
    )
    services.append(service_2)

    dataset3 = DatasetFactory(organisation=org)
    # operating_period_end_date is None
    txc_file_3 = TXCFileAttributesFactory(
        revision=dataset3.live_revision,
        service_code=service_codes[3],
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 28),
        line_names=[service_numbers[3]],
        filename="test3.xml",
    )
    # is_stale: staleness_12_months_old = True => "Stale - 12 months old"
    service_3 = ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[3],
        service_number=service_numbers[3],
        effective_date=datetime.datetime(2021, 1, 28),
        variation_number=3,
        start_point="start point service 3",
        finish_point="finish point service 3",
        via="via service 3",
        service_type_other_details="service type detail service 3",
        description="description service 3",
        operator=operator_factory,
        service_type_description="service type description service 3",
    )
    services.append(service_3)
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[3][-1:],
        start=datetime.datetime(2022, 2, 28),
        end=datetime.datetime(2024, 2, 28),
    )

    ui_lta = UILtaFactory(name="UI_LTA")

    LocalAuthorityFactory(
        id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    service_codes_csv = ComplianceReportCSV(org.id)
    csv_string = service_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    assert csv_output["row0"][0] == '"PD0001111:0"'
    assert csv_output["row0"][1] == '"Line0"'
    assert csv_output["row0"][2] == '"Registered"'
    assert csv_output["row0"][3] == '"In Scope"'
    assert csv_output["row0"][4] == '"In Season"'
    assert csv_output["row0"][5] == '"test_org_1"'
    assert csv_output["row0"][6] == '"Yes"'
    assert csv_output["row0"][7] == '"Yes"'
    assert csv_output["row0"][8] == '"Published"'
    assert csv_output["row0"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row0"][10] == '"Under maintenance"'
    assert csv_output["row0"][11] == '"Yes"'
    assert csv_output["row0"][12] == '"No"'
    assert csv_output["row0"][13] == '"No"'
    assert csv_output["row0"][14] == '"Yes"'
    assert csv_output["row0"][15] == '"Unpublished"'
    assert csv_output["row0"][16] == '"Not Stale"'
    assert csv_output["row0"][17] == '"No"'
    assert csv_output["row0"][18] == f'"{dataset0.id}"'
    assert csv_output["row0"][19] == '"test0.xml"'
    assert csv_output["row0"][20] == f'"{txc_file_0.national_operator_code}"'
    assert csv_output["row0"][21] == '"2022-01-28"'
    assert csv_output["row0"][22] == '"2023-01-28"'
    assert csv_output["row0"][23] == '"2023-06-28"'
    assert csv_output["row0"][24] == '""'
    assert csv_output["row0"][25] == '""'
    assert csv_output["row0"][26] == '""'
    assert csv_output["row0"][27] == '""'
    assert csv_output["row0"][28] == '""'
    assert csv_output["row0"][29] == '"2023-12-17"'
    assert csv_output["row0"][30] == '"2023-04-11"'
    assert csv_output["row0"][31] == '"2022-01-17"'
    assert csv_output["row0"][32] == '"2022-02-28"'
    assert csv_output["row0"][33] == '"2024-02-28"'
    assert csv_output["row0"][34] == '"operator"'
    assert csv_output["row0"][35] == '"PD0001111"'
    assert csv_output["row0"][36] == '"service type description service 0"'
    assert csv_output["row0"][37] == '"0"'
    assert csv_output["row0"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row0"][39] == '"2024-01-28"'
    assert csv_output["row0"][40] == f'"{service_0.received_date}"'
    assert csv_output["row0"][41] == '"South East"'
    assert csv_output["row0"][42] == '"UI_LTA"'

    assert csv_output["row1"][0] == '"PD0001111:1"'
    assert csv_output["row1"][1] == '"Line1"'
    assert csv_output["row1"][2] == '"Registered"'
    assert csv_output["row1"][3] == '"In Scope"'
    assert csv_output["row1"][4] == '"Out of Season"'
    assert csv_output["row1"][5] == '"test_org_1"'
    assert csv_output["row1"][6] == '"No"'
    assert csv_output["row1"][7] == '"No"'
    assert csv_output["row1"][8] == '"Published"'
    assert csv_output["row1"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row1"][10] == '"Under maintenance"'
    assert csv_output["row1"][11] == '"Yes"'
    assert csv_output["row1"][12] == '"No"'
    assert csv_output["row1"][13] == '"No"'
    assert csv_output["row1"][14] == '"Yes"'
    assert csv_output["row1"][15] == '"Unpublished"'
    assert csv_output["row1"][16] == '"Not Stale"'
    assert csv_output["row1"][17] == '"No"'
    assert csv_output["row1"][18] == f'"{dataset1.id}"'
    assert csv_output["row1"][19] == '"test1.xml"'
    assert csv_output["row1"][20] == f'"{txc_file_1.national_operator_code}"'
    assert csv_output["row1"][21] == '"2022-01-24"'
    assert csv_output["row1"][22] == '"2023-01-24"'
    assert csv_output["row1"][23] == '"2023-06-24"'
    assert csv_output["row1"][24] == '""'
    assert csv_output["row1"][25] == '""'
    assert csv_output["row1"][26] == '""'
    assert csv_output["row1"][27] == '""'
    assert csv_output["row1"][28] == '""'
    assert csv_output["row1"][29] == '"2023-12-13"'
    assert csv_output["row1"][30] == '"2023-04-11"'
    assert csv_output["row1"][31] == '"2026-01-17"'
    assert csv_output["row1"][32] == '"2026-02-28"'
    assert csv_output["row1"][33] == '"2028-02-28"'
    assert csv_output["row1"][34] == '"operator"'
    assert csv_output["row1"][35] == '"PD0001111"'
    assert csv_output["row1"][36] == '"service type description service 1"'
    assert csv_output["row1"][37] == '"1"'
    assert csv_output["row1"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row1"][39] == '"2024-01-24"'
    assert csv_output["row1"][40] == f'"{service_1.received_date}"'
    assert csv_output["row1"][41] == '"South East"'
    assert csv_output["row1"][42] == '"UI_LTA"'

    assert csv_output["row2"][0] == '"PD0001111:2"'
    assert csv_output["row2"][1] == '"Line2"'
    assert csv_output["row2"][2] == '"Registered"'
    assert csv_output["row2"][3] == '"In Scope"'
    assert csv_output["row2"][4] == '"Not Seasonal"'
    assert csv_output["row2"][5] == '"test_org_1"'
    assert csv_output["row2"][6] == '"Yes"'
    assert csv_output["row2"][7] == '"Yes"'
    assert csv_output["row2"][8] == '"Published"'
    assert csv_output["row2"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row2"][10] == '"Under maintenance"'
    assert csv_output["row2"][11] == '"Yes"'
    assert csv_output["row2"][12] == '"No"'
    assert csv_output["row2"][13] == '"No"'
    assert csv_output["row2"][14] == '"Yes"'
    assert csv_output["row2"][15] == '"Unpublished"'
    assert csv_output["row2"][16] == '"Not Stale"'
    assert csv_output["row2"][17] == '"No"'
    assert csv_output["row2"][18] == f'"{dataset2.id}"'
    assert csv_output["row2"][19] == '"test2.xml"'
    assert csv_output["row2"][20] == f'"{txc_file_2.national_operator_code}"'
    assert csv_output["row2"][21] == '"2022-01-24"'
    assert csv_output["row2"][22] == '"2023-01-24"'
    assert csv_output["row2"][23] == '"2023-06-24"'
    assert csv_output["row2"][24] == '""'
    assert csv_output["row2"][25] == '""'
    assert csv_output["row2"][26] == '""'
    assert csv_output["row2"][27] == '""'
    assert csv_output["row2"][28] == '""'
    assert csv_output["row2"][29] == '"2023-12-13"'
    assert csv_output["row2"][30] == '"2023-04-11"'
    assert csv_output["row2"][31] == '""'
    assert csv_output["row2"][32] == '""'
    assert csv_output["row2"][33] == '""'
    assert csv_output["row2"][34] == '"operator"'
    assert csv_output["row2"][35] == '"PD0001111"'
    assert csv_output["row2"][36] == '"service type description service 2"'
    assert csv_output["row2"][37] == '"2"'
    assert csv_output["row2"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row2"][39] == '"2024-01-24"'
    assert csv_output["row2"][40] == f'"{service_2.received_date}"'
    assert csv_output["row2"][41] == '"South East"'
    assert csv_output["row2"][42] == '"UI_LTA"'

    assert csv_output["row3"][0] == '"PD0001111:3"'
    assert csv_output["row3"][1] == '"Line3"'
    assert csv_output["row3"][2] == '"Registered"'
    assert csv_output["row3"][3] == '"In Scope"'
    assert csv_output["row3"][4] == '"In Season"'
    assert csv_output["row3"][5] == '"test_org_1"'
    assert csv_output["row3"][6] == '"Yes"'
    assert csv_output["row3"][7] == '"Yes"'
    assert csv_output["row3"][8] == '"Published"'
    assert csv_output["row3"][9] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row3"][10] == '"Under maintenance"'
    assert csv_output["row3"][11] == '"Yes"'
    assert csv_output["row3"][12] == '"No"'
    assert csv_output["row3"][13] == '"No"'
    assert csv_output["row3"][14] == '"Yes"'
    assert csv_output["row3"][15] == '"Unpublished"'
    assert csv_output["row3"][16] == '"Not Stale"'
    assert csv_output["row3"][17] == '"No"'
    assert csv_output["row3"][18] == f'"{dataset3.id}"'
    assert csv_output["row3"][19] == '"test3.xml"'
    assert csv_output["row3"][20] == f'"{txc_file_3.national_operator_code}"'
    assert csv_output["row3"][21] == '"2022-01-28"'
    assert csv_output["row3"][22] == '"2023-01-28"'
    assert csv_output["row3"][23] == '""'
    assert csv_output["row3"][24] == '""'
    assert csv_output["row3"][25] == '""'
    assert csv_output["row3"][26] == '""'
    assert csv_output["row3"][27] == '""'
    assert csv_output["row3"][28] == '""'
    assert csv_output["row3"][29] == '"2020-12-17"'
    assert csv_output["row3"][30] == '"2023-04-11"'
    assert csv_output["row3"][31] == '"2022-01-17"'
    assert csv_output["row3"][32] == '"2022-02-28"'
    assert csv_output["row3"][33] == '"2024-02-28"'
    assert csv_output["row3"][34] == '"operator"'
    assert csv_output["row3"][35] == '"PD0001111"'
    assert csv_output["row3"][36] == '"service type description service 3"'
    assert csv_output["row3"][37] == '"3"'
    assert csv_output["row3"][38] == f'"{otc_lic.expiry_date}"'
    assert csv_output["row3"][39] == '"2021-01-28"'
    assert csv_output["row3"][40] == f'"{service_3.received_date}"'
    assert csv_output["row3"][41] == '"South East"'
    assert csv_output["row3"][42] == '"UI_LTA"'
