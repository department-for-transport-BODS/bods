from enum import StrEnum, unique

from transit_odp.common.utils.choice_enum import ChoiceEnum


@unique
class AVLFeedStatus(ChoiceEnum):
    live = "FEED_UP"
    inactive = "FEED_DOWN"
    error = "SYSTEM_ERROR"


@unique
class ValidationTaskResultStatus(StrEnum):
    DEPLOYING = "DEPLOYING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    FEED_VALID = "FEED_VALID"
    FEED_INVALID = "FEED_INVALID"
