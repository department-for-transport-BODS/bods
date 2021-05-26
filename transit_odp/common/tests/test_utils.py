import datetime

import pytz

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
