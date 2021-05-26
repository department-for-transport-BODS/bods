import enum


@enum.unique
class FeedErrorSeverity(enum.Enum):
    severe = "severe"
    minor = "minor"


@enum.unique
class FeedErrorCategory(enum.Enum):
    xml = "xml"
    zip = "zip"
    naptan = "naptan"
    unknown = "unknown"
    data = "data"
    availability = "availability"


@enum.unique
class FeedNotificationCategory(enum.Enum):
    no_notifications = "no_notifications"
    immediately = "immediately"
    daily = "daily"
    weekly = "weekly"
