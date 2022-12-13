from enum import Enum, unique

from transit_odp.common.utils.choice_enum import ChoiceEnum


# TODO: for Python 3.11 use StrEnum class instead of (str, Enum)
@unique
class AVLFeedStatus(ChoiceEnum):
    DEPLOYING = "DEPLOYING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    FEED_UP = "FEED_UP"
    FEED_DOWN = "FEED_DOWN"


AVL_FEED_UP = AVLFeedStatus.FEED_UP.value
AVL_FEED_DOWN = AVLFeedStatus.FEED_DOWN.value
AVL_FEED_SYSTEM_ERROR = AVLFeedStatus.SYSTEM_ERROR.value
AVL_FEED_DEPLOYING = AVLFeedStatus.DEPLOYING.value


@unique
class ValidationTaskResultStatus(str, Enum):
    DEPLOYING = "DEPLOYING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    FEED_VALID = "FEED_VALID"
    FEED_INVALID = "FEED_INVALID"
