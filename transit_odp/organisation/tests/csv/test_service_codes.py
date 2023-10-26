from typing import Dict

import pytest
from django.db.models.expressions import datetime
from freezegun import freeze_time

from transit_odp.organisation.csv.service_codes import ServiceCodesCSV
from transit_odp.organisation.factories import DatasetFactory
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    SeasonalServiceFactory,
    ServiceCodeExemptionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.constants import FLEXIBLE_REG, SCHOOL_OR_WORKS
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory

pytestmark = pytest.mark.django_db
CSV_NUMBER_COLUMNS = 25


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
    ServiceModelFactory(
        licence=otc_lic1,
        registration_number=registration_number1,
        service_type_description=FLEXIBLE_REG,
    )
    ServiceModelFactory(
        licence=otc_lic1,
        registration_number=registration_number1,
        service_type_description=SCHOOL_OR_WORKS,
    )

    licence_number2 = "PA000002"
    otc_lic2 = LicenceModelFactory(number=licence_number2)
    registration_number2 = f"{licence_number2}/1"
    registration_number3 = f"{licence_number2}/2"
    registration_number6 = f"{licence_number2}/3"
    ServiceModelFactory(licence=otc_lic2, registration_number=registration_number2)
    ServiceModelFactory(licence=otc_lic2, registration_number=registration_number3)
    ServiceModelFactory(licence=otc_lic2, registration_number=registration_number6)

    licence_number3 = "PB000003"
    otc_lic3 = LicenceModelFactory(number=licence_number3)
    registration_number4 = f"{licence_number3}/1"
    registration_number5 = f"{licence_number3}/2"
    ServiceModelFactory(licence=otc_lic3, registration_number=registration_number4)
    ServiceModelFactory(licence=otc_lic3, registration_number=registration_number5)

    org1 = OrganisationFactory()
    BODSLicenceFactory(organisation=org1, number=licence_number1)
    bods_lic = BODSLicenceFactory(organisation=org1, number=licence_number2)
    org2 = OrganisationFactory()
    BODSLicenceFactory(organisation=org2, number=licence_number3)

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

    service_codes_csv = ServiceCodesCSV(org1.id)
    queryset = service_codes_csv.get_queryset()

    assert len(queryset) == len(expected_pairs_org1)
    queryset_pairs = [
        (service["otc_licence_number"], service["otc_registration_number"])
        for service in queryset
    ]
    assert sorted(queryset_pairs) == sorted(expected_pairs_org1)


@freeze_time("2023-02-24")
def test_csv_output():
    licence_number = "PD0000099"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org1 = OrganisationFactory()
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)

    # Require Attention: No
    # TXCFileAttribute = None
    # SeasonalService = Not None and Out of Season
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[0],
        service_number=service_numbers[0],
        effective_date=datetime.datetime(2023, 6, 24),
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
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[1],
        service_number=service_numbers[1],
        effective_date=datetime.datetime(2023, 6, 24),
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
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[2],
        service_number=service_numbers[2],
        effective_date=datetime.datetime(2023, 6, 24),
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
        service_code=service_codes[3],
        licence_number=otc_lic.number,
        filename="test3.xml",
        operating_period_end_date=datetime.datetime(2023, 2, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    # staleness_otc = True => "Stale - OTC Variation"
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[3],
        service_number=service_numbers[3],
        effective_date=datetime.datetime(2023, 3, 24),
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
        service_code=service_codes[4],
        licence_number=otc_lic.number,
        filename="test4.xml",
        operating_period_end_date=datetime.datetime(2023, 3, 24),
        modification_datetime=datetime.datetime(2023, 1, 24),
    )
    # staleness_42_day_look_ahead = True => "Stale - 42 day look ahead"
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[4],
        service_number=service_numbers[4],
        effective_date=datetime.datetime(2022, 6, 24),
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
        service_code=service_codes[5],
        licence_number=otc_lic.number,
        filename="test5.xml",
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[5],
        service_number=service_numbers[5],
        effective_date=datetime.datetime(2024, 1, 24),
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
        service_code=service_codes[6],
        licence_number=otc_lic.number,
        filename="test6.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[6],
        service_number=service_numbers[6],
        effective_date=datetime.datetime(2021, 1, 24),
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
        service_code=service_codes[7],
        licence_number=otc_lic.number,
        filename="test7.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    # staleness_12_months_old = True => "Stale - 12 months old"
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[7],
        service_number=service_numbers[7],
        effective_date=datetime.datetime(2021, 1, 24),
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
        service_code=service_codes[8],
        licence_number=otc_lic.number,
        filename="test8.xml",
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2023, 2, 24),
    )
    # staleness_otc = False, staleness_42_day_look_ahead = False,
    # staleness_12_months_old = False => Not Stale
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[8],
        service_number=service_numbers[8],
        effective_date=datetime.datetime(2021, 1, 24),
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[8][-1:],
    )

    # Testing something that IS in BODS but not in OTC
    licence_number = "PD0000055"

    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset9 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
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

    service_codes_csv = ServiceCodesCSV(org1.id)
    csv_string = service_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    assert csv_output["header"] == [
        '"XML:Service Code"',
        '"XML:Line Name"',
        '"Requires Attention"',
        '"Published Status"',
        '"OTC Status"',
        '"Scope Status"',
        '"Seasonal Status"',
        '"Timeliness Status"',
        '"Dataset ID"',
        '"Date OTC variation needs to be published"',
        '"Date for complete 42 day look ahead"',
        '"Date when data is over 1 year old"',
        '"Date seasonal service should be published"',
        '"Seasonal Start Date"',
        '"Seasonal End Date"',
        '"XML:Filename"',
        '"XML:Last Modified Date"',
        '"XML:National Operator Code"',
        '"XML:Licence Number"',
        '"XML:Revision Number"',
        '"XML:Operating Period Start Date"',
        '"XML:Operating Period End Date"',
        '"OTC:Licence Number"',
        '"OTC:Registration Number"',
        '"OTC:Service Number"',
    ]
    assert csv_output["row0"][0] == '""'  # XML:Service Code
    assert csv_output["row0"][1] == '""'  # XML:Line Name
    assert csv_output["row0"][2] == '"No"'  # requires attention
    assert csv_output["row0"][3] == '"Unpublished"'  # published status
    assert csv_output["row0"][4] == '"Registered"'  # OTC status
    assert csv_output["row0"][5] == '"In Scope"'  # scope status
    assert csv_output["row0"][6] == '"Out of Season"'  # seasonal status
    assert csv_output["row0"][7] == '"Up to date"'  # timeliness status
    assert csv_output["row0"][8] == '""'  # dataset id
    assert csv_output["row0"][9] == '"2023-05-12"'
    # date OTC variation needs to be published
    assert csv_output["row0"][10] == '"2023-04-07"'
    # date for complete 42 day look ahead
    assert csv_output["row0"][11] == '""'
    # Date when data is over 1 year old
    assert csv_output["row0"][12] == '"2024-01-13"'
    # date seasonal service should be published
    assert csv_output["row0"][13] == '"2024-02-24"'  # seasonal start date
    assert csv_output["row0"][14] == '"2026-02-24"'  # seasonal end date
    assert csv_output["row0"][15] == '""'  # XML:Filename
    assert csv_output["row0"][16] == '""'  # XML:Last Modified Date
    assert csv_output["row0"][17] == '""'  # XML:National Operator Code
    assert csv_output["row0"][18] == '""'  # XML:Licence Number
    assert csv_output["row0"][19] == '""'  # XML:Revision Number
    assert csv_output["row0"][20] == '""'  # Operating Period Start Date
    assert csv_output["row0"][21] == '""'  # Operating Period End Date
    assert csv_output["row0"][22] == '"PD0000099"'  # OTC:Licence Number
    assert csv_output["row0"][23] == '"PD0000099:0"'  # OTC:Registration Number
    assert csv_output["row0"][24] == '"Line0"'  # OTC:Service Number

    assert csv_output["row1"][0] == '""'
    assert csv_output["row1"][1] == '""'
    assert csv_output["row1"][2] == '"Yes"'
    assert csv_output["row1"][3] == '"Unpublished"'
    assert csv_output["row1"][4] == '"Registered"'
    assert csv_output["row1"][5] == '"In Scope"'
    assert csv_output["row1"][6] == '"In Season"'
    assert csv_output["row1"][7] == '"Up to date"'
    assert csv_output["row1"][8] == '""'
    assert csv_output["row1"][9] == '"2023-05-12"'
    assert csv_output["row1"][10] == '"2023-04-07"'
    assert csv_output["row1"][11] == '""'
    assert csv_output["row1"][18] == '""'
    assert csv_output["row1"][19] == '""'
    assert csv_output["row1"][20] == '""'
    assert csv_output["row1"][21] == '""'
    assert csv_output["row1"][22] == '"PD0000099"'
    assert csv_output["row1"][23] == '"PD0000099:1"'
    assert csv_output["row1"][24] == '"Line1"'

    assert csv_output["row2"][0] == '""'
    assert csv_output["row2"][1] == '""'
    assert csv_output["row2"][2] == '"No"'
    assert csv_output["row2"][3] == '"Unpublished"'
    assert csv_output["row2"][4] == '"Registered"'
    assert csv_output["row2"][5] == '"Out of Scope"'
    assert csv_output["row2"][6] == '"Not Seasonal"'
    assert csv_output["row2"][7] == '"Up to date"'
    assert csv_output["row2"][8] == '""'
    assert csv_output["row2"][9] == '"2023-05-12"'
    assert csv_output["row2"][10] == '"2023-04-07"'
    assert csv_output["row2"][11] == '""'
    assert csv_output["row2"][12] == '""'
    assert csv_output["row2"][13] == '""'
    assert csv_output["row2"][14] == '""'
    assert csv_output["row2"][15] == '""'
    assert csv_output["row2"][16] == '""'
    assert csv_output["row2"][17] == '""'
    assert csv_output["row2"][18] == '""'
    assert csv_output["row2"][19] == '""'
    assert csv_output["row2"][20] == '""'
    assert csv_output["row2"][21] == '""'
    assert csv_output["row2"][22] == '"PD0000099"'
    assert csv_output["row2"][23] == '"PD0000099:2"'
    assert csv_output["row2"][24] == '"Line2"'

    assert csv_output["row3"][0] == '"PD0000099:3"'
    assert csv_output["row3"][1] == '"line1 line2"'
    assert csv_output["row3"][2] == '"Yes"'
    assert csv_output["row3"][3] == '"Published"'
    assert csv_output["row3"][4] == '"Registered"'
    assert csv_output["row3"][5] == '"In Scope"'
    assert csv_output["row3"][6] == '"In Season"'
    assert csv_output["row3"][7] == '"OTC variation not published"'
    assert csv_output["row3"][8] == '"1"'
    assert csv_output["row3"][9] == '"2023-02-10"'
    assert csv_output["row3"][10] == '"2023-04-07"'
    assert csv_output["row3"][11] == '"2023-01-24"'
    assert csv_output["row3"][12] == '"2022-01-13"'
    assert csv_output["row3"][13] == '"2022-02-24"'
    assert csv_output["row3"][14] == '"2024-02-24"'
    assert csv_output["row3"][15] == '"test3.xml"'
    assert csv_output["row3"][16] == '"2022-01-24"'
    assert csv_output["row3"][18] == '"PD0000099"'
    assert csv_output["row3"][19] == '"0"'
    assert csv_output["row3"][21] == '"2023-02-24"'
    assert csv_output["row3"][22] == '"PD0000099"'
    assert csv_output["row3"][23] == '"PD0000099:3"'
    assert csv_output["row3"][24] == '"Line3"'

    assert csv_output["row4"][0] == '"PD0000099:4"'
    assert csv_output["row4"][1] == '"line1 line2"'
    assert csv_output["row4"][2] == '"Yes"'
    assert csv_output["row4"][3] == '"Published"'
    assert csv_output["row4"][4] == '"Registered"'
    assert csv_output["row4"][5] == '"In Scope"'
    assert csv_output["row4"][6] == '"In Season"'
    assert csv_output["row4"][7] == '"42 day look ahead is incomplete"'
    assert csv_output["row4"][8] == '"2"'
    assert csv_output["row4"][9] == '"2022-05-12"'
    assert csv_output["row4"][10] == '"2023-04-07"'
    assert csv_output["row4"][11] == '"2024-01-24"'
    assert csv_output["row4"][12] == '"2022-01-13"'
    assert csv_output["row4"][13] == '"2022-02-24"'
    assert csv_output["row4"][14] == '"2024-02-24"'
    assert csv_output["row4"][16] == '"2023-01-24"'
    assert csv_output["row4"][18] == '"PD0000099"'
    assert csv_output["row4"][23] == '"PD0000099:4"'
    assert csv_output["row4"][24] == '"Line4"'

    assert csv_output["row5"][0] == '"PD0000099:5"'
    assert csv_output["row5"][1] == '"line1 line2"'
    assert csv_output["row5"][2] == '"No"'
    assert csv_output["row5"][3] == '"Published"'
    assert csv_output["row5"][5] == '"In Scope"'
    assert csv_output["row5"][6] == '"In Season"'
    assert csv_output["row5"][7] == '"Up to date"'
    assert csv_output["row5"][8] == '"3"'
    assert csv_output["row5"][9] == '"2023-12-13"'
    assert csv_output["row5"][10] == '"2023-04-07"'
    assert csv_output["row5"][11] == '"2023-01-24"'
    assert csv_output["row5"][12] == '"2022-01-13"'
    assert csv_output["row5"][13] == '"2022-02-24"'
    assert csv_output["row5"][14] == '"2024-02-24"'
    assert csv_output["row5"][15] == '"test5.xml"'
    assert csv_output["row5"][16] == '"2022-01-24"'
    assert csv_output["row5"][22] == '"PD0000099"'
    assert csv_output["row5"][23] == '"PD0000099:5"'
    assert csv_output["row5"][24] == '"Line5"'

    assert csv_output["row6"][0] == '"PD0000099:6"'
    assert csv_output["row6"][1] == '"line1 line2"'
    assert csv_output["row6"][2] == '"Yes"'
    assert csv_output["row6"][3] == '"Published"'
    assert csv_output["row6"][4] == '"Registered"'
    assert csv_output["row6"][5] == '"In Scope"'
    assert csv_output["row6"][6] == '"In Season"'
    assert csv_output["row6"][7] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row6"][8] == '"4"'
    assert csv_output["row6"][9] == '"2020-12-13"'
    assert csv_output["row6"][10] == '"2023-04-07"'
    assert csv_output["row6"][11] == '"2023-01-24"'
    assert csv_output["row6"][12] == '"2022-01-13"'
    assert csv_output["row6"][13] == '"2022-02-24"'
    assert csv_output["row6"][14] == '"2024-02-24"'
    assert csv_output["row6"][15] == '"test6.xml"'
    assert csv_output["row6"][16] == '"2022-01-24"'
    assert csv_output["row6"][18] == '"PD0000099"'
    assert csv_output["row6"][19] == '"0"'
    assert csv_output["row6"][21] == '""'
    assert csv_output["row6"][22] == '"PD0000099"'
    assert csv_output["row6"][23] == '"PD0000099:6"'
    assert csv_output["row6"][24] == '"Line6"'

    assert csv_output["row7"][0] == '"PD0000099:7"'
    assert csv_output["row7"][1] == '"line1 line2"'
    assert csv_output["row7"][2] == '"No"'
    assert csv_output["row7"][3] == '"Published"'
    assert csv_output["row7"][4] == '"Registered"'
    assert csv_output["row7"][5] == '"Out of Scope"'
    assert csv_output["row7"][7] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row7"][8] == '"5"'
    assert csv_output["row7"][9] == '"2020-12-13"'
    assert csv_output["row7"][10] == '"2023-04-07"'
    assert csv_output["row7"][11] == '"2023-01-24"'
    assert csv_output["row7"][15] == '"test7.xml"'
    assert csv_output["row7"][16] == '"2022-01-24"'
    assert csv_output["row7"][18] == '"PD0000099"'
    assert csv_output["row7"][19] == '"0"'
    assert csv_output["row7"][21] == '""'
    assert csv_output["row7"][22] == '"PD0000099"'
    assert csv_output["row7"][23] == '"PD0000099:7"'
    assert csv_output["row7"][24] == '"Line7"'

    assert csv_output["row8"][0] == '"PD0000099:8"'
    assert csv_output["row8"][1] == '"line1 line2"'
    assert csv_output["row8"][2] == '"No"'
    assert csv_output["row8"][3] == '"Published"'
    assert csv_output["row8"][4] == '"Registered"'
    assert csv_output["row8"][5] == '"In Scope"'
    assert csv_output["row8"][7] == '"Up to date"'
    assert csv_output["row8"][8] == '"6"'
    assert csv_output["row8"][9] == '"2020-12-13"'
    assert csv_output["row8"][10] == '"2023-04-07"'
    assert csv_output["row8"][11] == '"2024-02-24"'
    assert csv_output["row8"][15] == '"test8.xml"'
    assert csv_output["row8"][16] == '"2023-02-24"'
    assert csv_output["row8"][18] == '"PD0000099"'
    assert csv_output["row8"][19] == '"0"'
    assert csv_output["row8"][21] == '""'
    assert csv_output["row8"][22] == '"PD0000099"'
    assert csv_output["row8"][23] == '"PD0000099:8"'
    assert csv_output["row8"][24] == '"Line8"'

    assert csv_output["row9"][0] == '"Z10"'
    assert csv_output["row9"][1] == '"line1 line2"'
    assert csv_output["row9"][2] == '"No"'
    assert csv_output["row9"][3] == '"Published"'
    assert csv_output["row9"][4] == '"Unregistered"'
    assert csv_output["row9"][5] == '"In Scope"'
    assert csv_output["row9"][6] == '"Not Seasonal"'
    assert csv_output["row9"][7] == '"Up to date"'
    assert csv_output["row9"][8] == '"7"'
    assert csv_output["row9"][9] == '""'
    assert csv_output["row9"][10] == '"2023-04-07"'
    assert csv_output["row9"][11] == '"2024-02-24"'
    assert csv_output["row9"][12] == '""'
    assert csv_output["row9"][13] == '""'
    assert csv_output["row9"][14] == '""'
    assert csv_output["row9"][15] == '"test9.xml"'
    assert csv_output["row9"][16] == '"2023-02-24"'
    assert csv_output["row9"][18] == '"PD0000055"'
    assert csv_output["row9"][19] == '"0"'
    assert csv_output["row9"][21] == '""'
    assert csv_output["row9"][22] == '""'
    assert csv_output["row9"][23] == '""'
    assert csv_output["row9"][24] == '""'


@freeze_time("2023-02-28")
def test_seasonal_status_csv_output():
    licence_number = "PD0001111"
    num_otc_services = 10
    service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
    service_numbers = [f"Line{n}" for n in range(num_otc_services)]

    org = OrganisationFactory()
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    otc_lic = LicenceModelFactory(number=licence_number)

    # Not Stale
    dataset0 = DatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset0.live_revision,
        service_code=service_codes[0],
        operating_period_end_date=datetime.datetime(2023, 6, 28),
        modification_datetime=datetime.datetime(2022, 1, 28),
    )
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[0],
        service_number=service_numbers[0],
        effective_date=datetime.datetime(2024, 1, 28),
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
        service_code=service_codes[1],
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[1],
        service_number=service_numbers[1],
        effective_date=datetime.datetime(2024, 1, 24),
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
        service_code=service_codes[2],
        operating_period_end_date=datetime.datetime(2023, 6, 24),
        modification_datetime=datetime.datetime(2022, 1, 24),
    )
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[2],
        service_number=service_numbers[2],
        effective_date=datetime.datetime(2024, 1, 24),
    )

    dataset3 = DatasetFactory(organisation=org)
    # operating_period_end_date is None
    TXCFileAttributesFactory(
        revision=dataset3.live_revision,
        service_code=service_codes[3],
        operating_period_end_date=None,
        modification_datetime=datetime.datetime(2022, 1, 28),
    )
    # is_stale: staleness_12_months_old = True => "Stale - 12 months old"
    ServiceModelFactory(
        licence=otc_lic,
        registration_number=service_codes[3],
        service_number=service_numbers[3],
        effective_date=datetime.datetime(2021, 1, 28),
    )
    # in season
    SeasonalServiceFactory(
        licence=bods_licence,
        registration_code=service_codes[3][-1:],
        start=datetime.datetime(2022, 2, 28),
        end=datetime.datetime(2024, 2, 28),
    )

    service_codes_csv = ServiceCodesCSV(org.id)
    csv_string = service_codes_csv.to_string()
    csv_output = get_csv_output(csv_string)

    assert csv_output["row0"][0] == '"PD0001111:0"'
    assert csv_output["row0"][1] == '"line1 line2"'
    assert csv_output["row0"][2] == '"No"'
    assert csv_output["row0"][3] == '"Published"'
    assert csv_output["row0"][4] == '"Registered"'
    assert csv_output["row0"][5] == '"In Scope"'
    assert csv_output["row0"][6] == '"In Season"'
    assert csv_output["row0"][7] == '"Up to date"'
    assert csv_output["row0"][8] == '"8"'
    assert csv_output["row0"][9] == '"2023-12-17"'
    assert csv_output["row0"][10] == '"2023-04-11"'
    assert csv_output["row0"][11] == '"2023-01-28"'
    assert csv_output["row0"][12] == '"2022-01-17"'
    assert csv_output["row0"][13] == '"2022-02-28"'
    assert csv_output["row0"][14] == '"2024-02-28"'
    assert csv_output["row0"][16] == '"2022-01-28"'
    assert csv_output["row0"][18] == '"PF0002280"'
    assert csv_output["row0"][19] == '"0"'
    assert csv_output["row0"][21] == '"2023-06-28"'
    assert csv_output["row0"][22] == '"PD0001111"'
    assert csv_output["row0"][23] == '"PD0001111:0"'
    assert csv_output["row0"][24] == '"Line0"'

    assert csv_output["row1"][0] == '"PD0001111:1"'
    assert csv_output["row1"][1] == '"line1 line2"'
    assert csv_output["row1"][2] == '"No"'
    assert csv_output["row1"][3] == '"Published"'
    assert csv_output["row1"][4] == '"Registered"'
    assert csv_output["row1"][5] == '"In Scope"'
    assert csv_output["row1"][6] == '"Out of Season"'
    assert csv_output["row1"][7] == '"Up to date"'
    assert csv_output["row1"][8] == '"9"'
    assert csv_output["row1"][9] == '"2023-12-13"'
    assert csv_output["row1"][10] == '"2023-04-11"'
    assert csv_output["row1"][11] == '"2023-01-24"'
    assert csv_output["row1"][12] == '"2026-01-17"'
    assert csv_output["row1"][13] == '"2026-02-28"'
    assert csv_output["row1"][14] == '"2028-02-28"'
    assert csv_output["row1"][16] == '"2022-01-24"'
    assert csv_output["row1"][18] == '"PF0002280"'
    assert csv_output["row1"][19] == '"0"'
    assert csv_output["row1"][21] == '"2023-06-24"'
    assert csv_output["row1"][22] == '"PD0001111"'
    assert csv_output["row1"][23] == '"PD0001111:1"'
    assert csv_output["row1"][24] == '"Line1"'

    assert csv_output["row2"][0] == '"PD0001111:2"'
    assert csv_output["row2"][1] == '"line1 line2"'
    assert csv_output["row2"][2] == '"No"'
    assert csv_output["row2"][3] == '"Published"'
    assert csv_output["row2"][4] == '"Registered"'
    assert csv_output["row2"][5] == '"In Scope"'
    assert csv_output["row2"][6] == '"Not Seasonal"'
    assert csv_output["row2"][7] == '"Up to date"'
    assert csv_output["row2"][8] == '"10"'
    assert csv_output["row2"][9] == '"2023-12-13"'
    assert csv_output["row2"][10] == '"2023-04-11"'
    assert csv_output["row2"][11] == '"2023-01-24"'
    assert csv_output["row2"][12] == '""'
    assert csv_output["row2"][13] == '""'
    assert csv_output["row2"][14] == '""'
    assert csv_output["row2"][16] == '"2022-01-24"'
    assert csv_output["row2"][18] == '"PF0002280"'
    assert csv_output["row2"][19] == '"0"'
    assert csv_output["row2"][21] == '"2023-06-24"'
    assert csv_output["row2"][22] == '"PD0001111"'
    assert csv_output["row2"][23] == '"PD0001111:2"'
    assert csv_output["row2"][24] == '"Line2"'

    assert csv_output["row3"][0] == '"PD0001111:3"'
    assert csv_output["row3"][1] == '"line1 line2"'
    assert csv_output["row3"][2] == '"Yes"'
    assert csv_output["row3"][3] == '"Published"'
    assert csv_output["row3"][4] == '"Registered"'
    assert csv_output["row3"][5] == '"In Scope"'
    assert csv_output["row3"][6] == '"In Season"'
    assert csv_output["row3"][7] == '"Service hasn\'t been updated within a year"'
    assert csv_output["row3"][8] == '"11"'
    assert csv_output["row3"][9] == '"2020-12-17"'
    assert csv_output["row3"][10] == '"2023-04-11"'
    assert csv_output["row3"][11] == '"2023-01-28"'
    assert csv_output["row3"][12] == '"2022-01-17"'
    assert csv_output["row3"][13] == '"2022-02-28"'
    assert csv_output["row3"][14] == '"2024-02-28"'
    assert csv_output["row3"][16] == '"2022-01-28"'
    assert csv_output["row3"][18] == '"PF0002280"'
    assert csv_output["row3"][19] == '"0"'
    assert csv_output["row3"][21] == '""'
    assert csv_output["row3"][22] == '"PD0001111"'
    assert csv_output["row3"][23] == '"PD0001111:3"'
    assert csv_output["row3"][24] == '"Line3"'
