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
