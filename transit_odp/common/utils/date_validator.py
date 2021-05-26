import logging
import re

from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

regex = (
    r"^(-?(?:[1-9][0-9]*)?[0-9]{4})-(1[0-2]|0[1-9])-"
    r"(3[01]|0[1-9]|[12][0-9])T(2[0-3]|[01][0-9]):([0-5][0-9]):"
    r"([0-5][0-9])(\.[0-9]+)?(Z|[+-](?:2[0-3]|[01][0-9]):[0-5][0-9])?$"
)


def validate(date_time_str):
    try:
        if re.compile(regex).match(date_time_str) is not None:
            return True
    except Exception:
        return False
    raise ValidationError(
        u"Provided datetime format is incorrect. Correct format: 'YYYY-MM-DDTHH:MM:SS'"
    )
