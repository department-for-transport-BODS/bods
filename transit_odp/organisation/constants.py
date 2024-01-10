import enum

from django.db.models.enums import TextChoices
from django.utils.translation import gettext_lazy as _

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


DELETED = FeedStatus.deleted.value
DRAFT = FeedStatus.draft.value
ERROR = FeedStatus.error.value
EXPIRED = FeedStatus.expired.value
INACTIVE = FeedStatus.inactive.value
LIVE = FeedStatus.live.value
PENDING = FeedStatus.pending.value
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

SEARCH_STATUS_CHOICES = (
    (LIVE, "Published"),
    (INACTIVE, "Inactive"),
)


class DatasetType(int, ChoiceEnum):
    TIMETABLE = 1
    AVL = 2
    FARES = 3
    DISRUPTIONS = 4


TimetableType = DatasetType.TIMETABLE.value
AVLType = DatasetType.AVL.value
FaresType = DatasetType.FARES.value
DisruptionsType = DatasetType.DISRUPTIONS.value

NO_ACTIVITY = "No vehicle activity"

DATASET_TYPE_NAMESPACE_MAP = {
    DatasetType.TIMETABLE: "",
    DatasetType.AVL: "avl",
    DatasetType.FARES: "fares",
    DatasetType.DISRUPTIONS: "disruptions",
}

DATASET_TYPE_PRETTY_MAP = {
    DatasetType.TIMETABLE: "Timetables",
    DatasetType.AVL: "Automatic Vehicle Locations",
    DatasetType.FARES: "Fares",
    DatasetType.DISRUPTIONS: "Disruptions",
}

PSV_LICENCE_ERROR_HINT_MESSAGE = (
    "The licence number should be in the format of two alpha values followed by 7 "
    "numeric values (e.g. PD0000123). If you have a pre-2000 licence, please add 4 "
    "zeros between the letters and numbers."
)
PSV_LICENCE_ERROR_MESSAGE = "Licence number entered with the wrong format"
PSV_LICENCE_AND_CHECKBOX = (
    "Enter a PSV licence number or check the box to confirm that there "
    "is no PSV licence number for this organisation"
)


class TravelineRegions(TextChoices):
    ALL = ("ALL", _("All"))
    EAST_ANGLIA = ("EA", _("East Anglia"))
    EAST_MIDLANDS = ("EM", _("East Midlands"))
    LONDON = ("L", _("London"))
    NORTH_EAST = ("NE", _("North East"))
    NORTH_WEST = ("NW", _("North West"))
    SCOTLAND = ("S", _("Scotland"))
    SOUTH_EAST = ("SE", _("South East"))
    SOUTH_WEST = ("SW", _("South West"))
    WALES = ("W", _("Wales"))
    WEST_MIDLANDS = ("WM", _("West Midlands"))
    YORKSHIRE = ("Y", _("Yorkshire"))


@enum.unique
class OrganisationStatus(ChoiceEnum):
    not_yet_invited = "Not yet invited"
    pending_invite = "Pending invite"
    active = "Active"
    inactive = "Inactive"


ORG_NOT_YET_INVITED = OrganisationStatus.not_yet_invited.value
ORG_PENDING_INVITE = OrganisationStatus.pending_invite.value
ORG_ACTIVE = OrganisationStatus.active.value
ORG_INACTIVE = OrganisationStatus.inactive.value
