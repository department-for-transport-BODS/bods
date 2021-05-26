import datetime

import pytest

from transit_odp.data_quality.factories import FastLinkWarningFactory
from transit_odp.data_quality.helpers import (
    construct_journey_overlap_message,
    convert_date_to_dmY_string,
    convert_time_to_HMS_string,
    create_comma_separated_string,
)


class TestCreateCommaSeparatedString:
    """
    Test create_comma_separated_string helper function, which should convert
    any iterable to a comma separated string.
    """

    # pytest seems to be super fussy about how you pass iterables to parametrize
    scenarios = (
        # list
        {"test_input": list(range(1, 10)), "expected_output": "1,2,3,4,5,6,7,8,9"},
        # tuple
        {
            "test_input": ("a", "b", "c", "d", "e", "f"),
            "expected_output": "a,b,c,d,e,f",
        },
        # empty iterable
        {"test_input": [], "expected_output": ""},
    )

    @pytest.mark.parametrize("scenario", [s for s in scenarios])
    def test_get_expected_string(self, scenario):
        output = create_comma_separated_string(scenario["test_input"])
        assert output == scenario["expected_output"]


class TestConvertDateToDmyString:
    scenarios = (
        (datetime.date(2020, 1, 8), "08/01/2020"),  # leading zeros
        (datetime.date(2020, 1, 30), "30/01/2020"),  # day then month
        (12345, "unknown date"),  # not a date object
    )

    @pytest.mark.parametrize(
        "test_input, expected_output",
        scenarios,
    )
    def test_returns_expected_date_string(self, test_input, expected_output):
        output = convert_date_to_dmY_string(test_input)
        assert output == expected_output


class TestConvertTimeToHmsString:
    scenarios = (
        (datetime.time(9, 5, 0), "09:05:00"),  # leading zeros
        (datetime.time(11, 59, 31), "11:59:31"),  # hour first
        (datetime.time(23, 12, 46), "23:12:46"),  # 24 hour clock
    )

    @pytest.mark.parametrize(
        "test_input, expected_output",
        scenarios,
    )
    def test_returns_expected_time_string(self, test_input, expected_output):
        output = convert_time_to_HMS_string(test_input)
        assert output == expected_output


class TestConstructJourneyOverlapMessage:
    # TODO: finish this test
    @pytest.mark.skip(reason="Can't test until VehicleJourneyFactory ready to use")
    def test_returns_expected_message(self):
        # warning factories don't yet have associated vehicle journeys
        warning = FastLinkWarningFactory.create()  # arbitrary warning type

        output = construct_journey_overlap_message(warning)
        expected_output = ""

        assert output == expected_output
