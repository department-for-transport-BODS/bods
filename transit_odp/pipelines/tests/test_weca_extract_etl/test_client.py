import json
from unittest.mock import patch
from requests.exceptions import HTTPError

import pytest
import requests_mock
from django.conf import settings

from transit_odp.pipelines.pipelines.weca_extract_etl.client import WecaClient


@pytest.fixture(autouse=True)
def mock_api_type_weca():
    with patch(
        "transit_odp.pipelines.pipelines.weca_extract_etl.client.API_TYPE_WECA", "WECA"
    ):
        yield


@pytest.fixture
def weca_registrations_data():
    registrations_data = {
        "fields": [
            {
                "id": "servicespt7_pk",
                "name": "ID:c1) Services",
                "desc": "Unique record identifier",
                "datatype": "BIGSERIAL",
                "category": "SEQUENCE",
            },
            {
                "id": "tenantid_sp",
                "name": "Operator ID",
                "desc": "For multi-tenanting",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "operatorlicence_istervices",
                "name": "Operator Licence Number",
                "desc": "{a1) Operators.Licence Number}",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "serialnum_ervi",
                "name": "Serial number",
                "desc": "{b1.0) new registrations.Serial number}",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "variation_ervi",
                "name": "Variation",
                "desc": "{new registration - calculate full serial number.Variation Number}",
                "datatype": "BIGINT",
                "category": "NUMBER",
            },
            {
                "id": "servicenumbers_icespt7a",
                "name": "Service numbers or names",
                "desc": "",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "startpoint_espt",
                "name": "Full address of service start point and NaPTAN",
                "desc": "",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "endpoint_sp",
                "name": "Full address of service finish point and NaPTAN",
                "desc": "",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "via_services_pt7atfu9e78z39yqc",
                "name": "Main points served on route (via)",
                "desc": "",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "typeofservice_stervice",
                "name": "Type Of Service",
                "desc": "case\n  when {c1) services.flexible bus service?} then 'Flexible'\n  else substring(\n    {c1) services.type of service}\n    from\n      4\n  )\nend",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "proposedstartda_istervices",
                "name": "Proposed Start Date",
                "desc": 'This calculation formats a date value as a string in "DD/MM/YYYY" format. It:\n\n1. Uses COALESCE to select the first non-null value between:\n   - mostrecentstartdatefromchangeregistration.mostrecentstartdate\n   - services.proposedstartdate\n\n2. Converts the selected date to a string with day/month/year components separated by slashes using the TO_CHAR function.',
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "enddate_sp",
                "name": "Proposed End Date (if applicable)",
                "desc": "",
                "datatype": "TIMESTAMP",
                "category": "DATE",
            },
            {
                "id": "qualifyingepser_istervices",
                "name": "Qualifying EP Services",
                "desc": "substring(\n  {c1) services.qualifying ep service(s)}\n  from\n    4\n)",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "subsidised_tervic",
                "name": "Subsidised",
                "desc": "Remove the first three characters from the text field 'is the service supported by subsidies from a local authority'",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "subsidisedby_stervice",
                "name": "Subsidised by",
                "desc": "case\nwhen {c1) services.west of england combined authority.}\nand {c1) services.north somerset council.} then 'West of England Combined Authority, North Somerset Council'\nwhen {c1) services.west of england combined authority.} then 'West of England Combined Authority'\nwhen {c1) services.north somerset council.} then 'North Somerset Council'\nend",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "granteddate_tervic",
                "name": "Granted Date",
                "desc": 'This calculation formats a timestamp value (`services.creationtimeauto`) into a date string with the format "DD/MM/YYYY" (day/month/year with forward slashes as separators). The `to_char` function converts the timestamp to text in the specified format.',
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "receiveddate_stervice",
                "name": "Received Date",
                "desc": "to_char(\n  coalesce(\n  greatest(\n    {b1.0) new registrations.notification 2 - date of new registration for weca},\n    {b1.0) new registrations.notification 3 - date of new registration for operator},\n    case\n      when {most recent notification 2 date from change registration.most recent change registration} > '01/01/2024':: timestamp then {most recent notification 2 date from change registration.most recent change registration}\n      else null\n    end\n  ),\n  {c1) services.date submitted}\n),\n  'DD' ||\n chr(47) ||\n 'MM' ||\n chr(47) ||\n 'YYYY'\n)\n\n\n",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "servicetype_tervic",
                "name": "Standard Or Flexible",
                "desc": "case\n  when {c1) services.flexible bus service?} then 'Flexible'\n  else 'Standard'\nend",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "trafficarea_tervic",
                "name": "Traffic Area",
                "desc": "'WECA'",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "applicationtype_istervices",
                "name": "Application Type",
                "desc": "case\n  when {c1) services.date of service cancellation} is not null then 'Cancellation'\n  else coalesce(\n    {b2.0) change or cancellation registration.application type},\n    'New'\n  )\nend",
                "datatype": "VARCHAR",
                "category": "TEXT",
            },
            {
                "id": "shortnotice_tervic",
                "name": "Short notice",
                "desc": "coalesce({most recent short notice from change registration.short notice (less than 42 days from proposed start date)}, {b1.0) new registrations.short notice (less than 42 days from proposed start date)})",
                "datatype": "BOOLEAN",
                "category": "CHECKBOX",
            },
        ],
        "data": [
            {
                "id": 734,
                "servicespt7_pk": "734",
                "tenantid_sp": "The Big Lemon C.I.C",
                "operatorlicence_istervices": "PH2058842",
                "serialnum_ervi": "PH2058842/01010012",
                "variation_ervi": "2",
                "servicenumbers_icespt7a": "61",
                "startpoint_espt": "140 Wick Rd, Brislington, Bristol BS4 4HQ",
                "endpoint_sp": "Gas Ferry Rd bus stop, Bristol BS1 5DZ",
                "via_services_pt7atfu9e78z39yqc": "Bloomfield Rd, Wicklea Academy, Sandy Park Rd, St Phillips Causeway, The Dings, Old Market, Broadmead, The Centre",
                "typeofservice_stervice": "Normal Stopping Service",
                "proposedstartda_istervices": "01/02/2025",
                "enddate_sp": "",
                "qualifyingepser_istervices": "Yes",
                "subsidised_tervic": "No",
                "subsidisedby_stervice": "",
                "granteddate_tervic": "23/08/2024",
                "receiveddate_stervice": "31/01/2025",
                "servicetype_tervic": "Standard",
                "trafficarea_tervic": "WECA",
                "applicationtype_istervices": "Cancellation",
                "shortnotice_tervic": "yes",
            },
            {
                "id": 819,
                "servicespt7_pk": "819",
                "tenantid_sp": "High Experiences Ltd",
                "operatorlicence_istervices": "PH2085119",
                "serialnum_ervi": "PH2085119/01010001",
                "variation_ervi": "2",
                "servicenumbers_icespt7a": "Bath City Tour",
                "startpoint_espt": "Bath Abbey /Terrace Walk 0180BAC30606 / 0180BAC30603",
                "endpoint_sp": "Bath Abbey /Terrace Walk 0180BAC30606 / 0180BAC30603",
                "via_services_pt7atfu9e78z39yqc": "Queens Square, Brock Street, Park Lane, Royal Avenue",
                "typeofservice_stervice": "Limited Stops",
                "proposedstartda_istervices": "01/06/2026",
                "enddate_sp": "30 Sept 2026",
                "qualifyingepser_istervices": "Yes",
                "subsidised_tervic": "No",
                "subsidisedby_stervice": "",
                "granteddate_tervic": "15/12/2025",
                "receiveddate_stervice": "26/03/2026",
                "servicetype_tervic": "Standard",
                "trafficarea_tervic": "WECA",
                "applicationtype_istervices": "Change",
                "shortnotice_tervic": "yes",
            },
            {
                "id": 643,
                "servicespt7_pk": "643",
                "tenantid_sp": "Stagecoach Devon Ltd",
                "operatorlicence_istervices": "PH1020951",
                "serialnum_ervi": "PH1020951/01010283",
                "variation_ervi": "0",
                "servicenumbers_icespt7a": "Forward Festival",
                "startpoint_espt": "Temple Meads (T6), Redcliffe, Bristol BS1 6QQ, UK 0100BRP90312",
                "endpoint_sp": "Black Boy Hill (A), Clifton, Bristol BS8 3HA, UK 0100BRA10941",
                "via_services_pt7atfu9e78z39yqc": "Queen Square, Bristol BS1 4QF, UK - on return Journey return Via Baldwin Street. Each direction serving Whiteladies Road",
                "typeofservice_stervice": "Limited Stops",
                "proposedstartda_istervices": "01/09/2023",
                "enddate_sp": "02 Sept 2023",
                "qualifyingepser_istervices": "No",
                "subsidised_tervic": "No",
                "subsidisedby_stervice": "",
                "granteddate_tervic": "01/08/2023",
                "receiveddate_stervice": "18/07/2023",
                "servicetype_tervic": "Standard",
                "trafficarea_tervic": "WECA",
                "applicationtype_istervices": "New",
                "shortnotice_tervic": "no",
            },
        ],
    }
    yield registrations_data


@pytest.fixture
def weca_get_registrations_data(weca_registrations_data):
    with requests_mock.Mocker() as mock:
        data = json.loads(weca_registrations_data)
        mock.post(
            f"{settings.WECA_API_URL}?c={settings.WECA_PARAM_C_REGISTRATIONS}&t={settings.WECA_PARAM_T_REGISTRATIONS}&r={settings.WECA_PARAM_R_REGISTRATIONS}&get_report_json=true&json_format=json",
            json=data,
        )
    yield mock


def test_weca_api_registrations_response_returned(weca_get_registrations_data):
    with weca_get_registrations_data:
        client = WecaClient()
        response = client.fetch_weca_registrations()
        assert len(response.data) == 3
        assert len(response.fields) == 21


@patch("django.conf.settings.WECA_PARAM_C_REGISTRATIONS", "dummay_weca_param_c")
def test_weca_api_registrations_response_error():
    with pytest.raises(HTTPError) as e:
        client = WecaClient()
        response = client.fetch_weca_registrations()
