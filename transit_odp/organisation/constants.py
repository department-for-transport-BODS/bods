import enum

from transit_odp.common.utils.choice_enum import ChoiceEnum


@enum.unique
class FeedStatus(ChoiceEnum):
    pending = "pending"
    draft = "draft"
    indexing = "indexing"
    live = "live"
    success = "success"
    expiring = "expiring"
    warning = "warning"
    error = "error"
    expired = "expired"
    deleted = "deleted"
    inactive = "inactive"

    def is_public(self):
        return (self == self.live) or (self == self.expiring) or (self == self.warning)


PENDING = FeedStatus.pending.value
EXPIRED = FeedStatus.expired.value
LIVE = FeedStatus.live.value
ERROR = FeedStatus.error.value
INACTIVE = FeedStatus.inactive.value
DELETED = FeedStatus.deleted.value
SUCCESS = FeedStatus.success.value

EXPIRY_NOTIFY_THRESHOLD = 30

# We use the same display value for multiple db values (see status_indicator.html)
STATUS_CHOICES = (
    (FeedStatus.pending.value, "Pending"),
    (FeedStatus.draft.value, "Draft"),
    (FeedStatus.indexing.value, "Processing"),
    (FeedStatus.live.value, "Published"),
    (FeedStatus.success.value, "Draft"),
    (FeedStatus.expiring.value, "Soon to expire"),
    (FeedStatus.warning.value, "Warning"),
    (FeedStatus.error.value, "Error"),
    (FeedStatus.expired.value, "Expired"),
    (FeedStatus.deleted.value, "Deleted"),
    (FeedStatus.inactive.value, "Inactive"),
)


@enum.unique
class AVLFeedStatus(ChoiceEnum):
    DEPLOYING = "DEPLOYING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    FEED_UP = "FEED_UP"
    FEED_DOWN = "FEED_DOWN"


class DatasetType(int, ChoiceEnum):
    TIMETABLE = 1
    AVL = 2
    FARES = 3


TimetableType = DatasetType.TIMETABLE.value
AVLType = DatasetType.AVL.value
FaresType = DatasetType.FARES.value

AVLFeedUp = AVLFeedStatus.FEED_UP.value
AVLFeedDown = AVLFeedStatus.FEED_DOWN.value
AVLFEEDSystemError = AVLFeedStatus.SYSTEM_ERROR.value
AVLFeedDeploying = AVLFeedStatus.DEPLOYING.value

DATASET_TYPE_NAMESPACE_MAP = {
    DatasetType.TIMETABLE: "",
    DatasetType.AVL: "avl",
    DatasetType.FARES: "fares",
}

DATASET_TYPE_PRETTY_MAP = {
    DatasetType.TIMETABLE: "Timetables",
    DatasetType.AVL: "Automatic Vehicle Locations",
    DatasetType.FARES: "Fares",
}

PSV_LICENCE_ERROR_HINT_MESSAGE = (
    "The licence number should be in the format of two alpha values followed by 7 "
    "numeric values (e.g. PD0000123). If you have a pre-2000 licence, please add 4 "
    "zeros between the letters and numbers."
)
PSV_LICENCE_ERROR_MESSAGE = "Licence number entered with the wrong format"
