import pandas as pd
import pytest

from unittest.mock import MagicMock, patch
from requests import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from transit_odp.timetables.utils import get_bank_holidays
from transit_odp.transmodel.models import BankHolidays

from pydantic import ValidationError


@patch("transit_odp.timetables.utils.requests")
def test_get_data_from_api(mrequests):
    json_content = {
        "england-and-wales": {
            "division": "england-and-wales",
            "events": [
                {
                    "title": "New Year's Day",
                    "date": "2018-01-01",
                    "notes": "",
                    "bunting": True,
                },
                {
                    "title": "Good Friday",
                    "date": "2018-03-30",
                    "notes": "",
                    "bunting": False,
                },
            ],
        },
        "scotland": {
            "division": "scotland",
            "events": [
                {
                    "title": "New Year's Day",
                    "date": "2018-01-01",
                    "notes": "",
                    "bunting": True,
                }
            ],
        },
    }

    mresponse = MagicMock(status_code=HTTP_200_OK)
    mresponse.json.return_value = json_content
    mrequests.get.return_value = mresponse
    column_names = [field.name for field in BankHolidays._meta.fields]

    holidays = get_bank_holidays()

    df_holidays = pd.DataFrame(holidays, columns=column_names)
    divisions = df_holidays["division"].unique()

    assert any(df_holidays["txc_element"] == "NewYearsEve")
    assert set(divisions) == {"england-and-wales", "scotland"}


@patch("transit_odp.timetables.utils.requests")
def test_error_response_from_api(mrequests):
    json_content = {}
    mresponse = MagicMock(status_code=HTTP_400_BAD_REQUEST)
    mresponse.json.return_value = json_content
    mrequests.get.return_value = mresponse
    column_names = [field.name for field in BankHolidays._meta.fields]

    with pytest.raises(ValidationError) as api_exception:
        get_bank_holidays()

    assert api_exception.value.errors()


@patch("transit_odp.timetables.utils.requests")
def test_error_when_no_scotland_from_api(mrequests):
    json_content = {
        "england-and-wales": {
            "division": "england-and-wales",
            "events": [
                {
                    "title": "New Year's Day",
                    "date": "2018-01-01",
                    "notes": "",
                    "bunting": True,
                }
            ],
        }
    }
    mresponse = MagicMock(status_code=HTTP_200_OK)
    mresponse.json.return_value = json_content
    mrequests.get.return_value = mresponse

    with pytest.raises(ValidationError) as api_exception:
        get_bank_holidays()

    assert api_exception.value.errors()


@patch("transit_odp.timetables.utils.requests")
def test_error_when_no_england_and_wales_from_api(mrequests):
    json_content = {
        "scotland": {
            "division": "scotland",
            "events": [
                {
                    "title": "New Year's Day",
                    "date": "2018-01-01",
                    "notes": "",
                    "bunting": True,
                }
            ],
        }
    }
    mresponse = MagicMock(status_code=HTTP_200_OK)
    mresponse.json.return_value = json_content
    mrequests.get.return_value = mresponse

    with pytest.raises(ValidationError) as api_exception:
        get_bank_holidays()

    assert api_exception.value.errors()


@patch("transit_odp.timetables.utils.requests")
def test_substitute_records_from_api(mrequests):
    json_content = {
        "england-and-wales": {
            "division": "england-and-wales",
            "events": [
                {
                    "title": "New Year's Day",
                    "date": "2018-01-01",
                    "notes": "Substitute day",
                    "bunting": True,
                },
                {
                    "title": "Good Friday",
                    "date": "2018-03-30",
                    "notes": "",
                    "bunting": False,
                },
            ],
        },
        "scotland": {
            "division": "scotland",
            "events": [
                {
                    "title": "Christmas Day",
                    "date": "2018-12-25",
                    "notes": "Substitute day",
                    "bunting": True,
                }
            ],
        },
    }

    mresponse = MagicMock(status_code=HTTP_200_OK)
    mresponse.json.return_value = json_content
    mrequests.get.return_value = mresponse
    column_names = [field.name for field in BankHolidays._meta.fields]

    holidays = get_bank_holidays()

    df_holidays = pd.DataFrame(holidays, columns=column_names)
    divisions = df_holidays["division"].unique()

    assert any(df_holidays["txc_element"] == "NewYearsEve")
    assert any(df_holidays["txc_element"] == "ChristmasEve")
    assert any(df_holidays["txc_element"] == "NewYearsDayHoliday")
    assert any(df_holidays["txc_element"] == "ChristmasDayHoliday")
    assert set(divisions) == {"england-and-wales", "scotland"}


@patch("transit_odp.timetables.utils.requests")
def test_other_substitute_records_from_api(mrequests):
    json_content = {
        "england-and-wales": {
            "division": "england-and-wales",
            "events": [
                {
                    "title": "Boxing Day",
                    "date": "2018-12-27",
                    "notes": "Substitute day",
                    "bunting": True,
                },
            ],
        },
        "scotland": {
            "division": "scotland",
            "events": [
                {
                    "title": "2nd January",
                    "date": "2018-01-02",
                    "notes": "Substitute day",
                    "bunting": True,
                },
                {
                    "title": "St Andrew's Day",
                    "date": "2018-11-30",
                    "notes": "",
                    "bunting": False,
                },
            ],
        },
    }

    mresponse = MagicMock(status_code=HTTP_200_OK)
    mresponse.json.return_value = json_content
    mrequests.get.return_value = mresponse
    column_names = [field.name for field in BankHolidays._meta.fields]

    holidays = get_bank_holidays()

    df_holidays = pd.DataFrame(holidays, columns=column_names)

    assert set(df_holidays["txc_element"]) == {
        "BoxingDayHoliday",
        "Jan2ndScotlandHoliday",
        "StAndrewsDay",
    }


@patch("transit_odp.timetables.utils.requests")
def test_eve_records_from_api(mrequests):
    json_content = {
        "england-and-wales": {
            "division": "england-and-wales",
            "events": [
                {
                    "title": "New Year's Day",
                    "date": "2018-01-01",
                    "notes": "Substitute day",
                    "bunting": True,
                },
            ],
        },
        "scotland": {
            "division": "scotland",
            "events": [
                {
                    "title": "Christmas Day",
                    "date": "2018-12-25",
                    "notes": "Substitute day",
                    "bunting": True,
                }
            ],
        },
    }

    mresponse = MagicMock(status_code=HTTP_200_OK)
    mresponse.json.return_value = json_content
    mrequests.get.return_value = mresponse
    column_names = [field.name for field in BankHolidays._meta.fields]

    holidays = get_bank_holidays()

    df_holidays = pd.DataFrame(holidays, columns=column_names)

    assert set(df_holidays["txc_element"]) == {
        "NewYearsEve",
        "ChristmasEve",
        "NewYearsDayHoliday",
        "ChristmasDayHoliday",
    }
