from enum import Enum, unique

from transit_odp.common.utils.choice_enum import ChoiceEnum


# TODO: for Python 3.11 use StrEnum class instead of (str, Enum)
@unique
class AVLFeedStatus(ChoiceEnum):
    live = "FEED_UP"
    inactive = "FEED_DOWN"
    error = "SYSTEM_ERROR"


@unique
class ValidationTaskResultStatus(str, Enum):
    DEPLOYING = "DEPLOYING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    FEED_VALID = "FEED_VALID"
    FEED_INVALID = "FEED_INVALID"
