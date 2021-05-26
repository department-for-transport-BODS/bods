# Returns the earliest of first or second.
# If both are None, returns None
# If one is None, returns the other
import datetime


def earlier_or_later(first: datetime, second: datetime, choose_earlier=True):
    if first and second:
        return min(first, second) if choose_earlier else max(first, second)
    return first or second
