from unittest import TestCase

from rest_framework.exceptions import ValidationError

from transit_odp.common.utils.date_validator import validate


class TestDateTimeValidator(TestCase):
    def test_date_time_incorrect(self):
        test_date_time = "2017-01-01"
        self.assertRaises(ValidationError, validate, test_date_time)

    def test_date_time_correct1(self):
        test_date_time = "2008-08-30T01:45:36.123Z"
        assert validate(test_date_time) is True

    def test_date_time_correct2(self):
        test_date_time = "2016-12-13T21:20:37.593194+00:00"
        assert validate(test_date_time) is True
