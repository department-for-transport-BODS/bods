import datetime

from dateutil import tz

TZ = tz.gettz("Europe/London")


def empty_timestamp():
    # Don't use sentinel value to represent empty timestamps, since Pandas throws
    # OutOfBoundsDatetime errors
    # return datetime.datetime(9999, 9, 9, tzinfo=TZ)
    return None


def starting_timestamp():
    return datetime.datetime(1900, 9, 9, tzinfo=TZ)
