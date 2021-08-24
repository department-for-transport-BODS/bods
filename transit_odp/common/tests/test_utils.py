import datetime

import pytest
import pytz

from transit_odp.common.utils import (
    get_dataset_type_from_path_info,
    remove_query_string_param,
)
from transit_odp.common.utils.convert_datetime import (
    localize_datetime_and_convert_to_string,
)


class TestConvertDatetime:
    def test_convert_when_GMT(self):
        # Daylight saving time ended 27/10/19
        dt = datetime.datetime(2019, 10, 30, 00, 00, tzinfo=pytz.UTC)  # as stored in db

        assert localize_datetime_and_convert_to_string(dt) == "30-10-2019 00:00"

    def test_convert_when_BST(self):
        # Daylight saving time ended 27/10/19
        dt = datetime.datetime(2019, 10, 24, 23, 00, tzinfo=pytz.UTC)  # as stored in db

        assert localize_datetime_and_convert_to_string(dt) == "25-10-2019 00:00"


def test_remove_query_string_param():
    """
    GIVEN: a query_string param with the API key
    WHEN: we call remove_query_string_param
    THEN: the string that return shouldn't contain the api key
    """
    expected = "boundingBox=-1.580349%2C50.863892%2C-1.299683%2C50.979023"
    test_input = expected + "&api_key=67342c10a41de3be7830a40cea498c02a8b24761"

    result = remove_query_string_param(test_input, "api_key")

    assert expected == result


@pytest.mark.parametrize(
    "path_info,expected",
    [
        ("/api/v1/datafeed/", "SIRI VM"),
        ("/v1/gtfsrtdatafeed/", "GTFS RT"),
        ("/fares/", "Fares"),
        ("/api/v1/dataset/", "Timetable"),
        ("bla", ""),
    ],
)
def test_get_dataset_type_from_path_info(path_info, expected):
    """
    GIVEN: path_info
    WHEN: call get_dataset_type_from_path_info
    THEN: the correct dataset type
    """

    result = get_dataset_type_from_path_info(path_info)

    assert result == expected
