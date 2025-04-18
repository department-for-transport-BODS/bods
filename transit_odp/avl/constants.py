from django.conf import settings

from transit_odp.avl.enums import AVLFeedStatus

UNDERGOING = "Undergoing validation"
PARTIALLY_COMPLIANT = "Partially compliant"
AWAITING_REVIEW = "Awaiting publisher review"
COMPLIANT = "Compliant"
NON_COMPLIANT = "Non-compliant"
MORE_DATA_NEEDED = "Unavailable due to dormant feed"
VALIDATION_TERMINATED = "Validation terminated"
PENDING = "Pending"

COMPLIANCE_STATUS_CHOICES = [
    (UNDERGOING, UNDERGOING),
    (PARTIALLY_COMPLIANT, PARTIALLY_COMPLIANT),
    (AWAITING_REVIEW, AWAITING_REVIEW),
    (COMPLIANT, COMPLIANT),
    (NON_COMPLIANT, NON_COMPLIANT),
    (MORE_DATA_NEEDED, MORE_DATA_NEEDED),
    (VALIDATION_TERMINATED, VALIDATION_TERMINATED),
]

NEEDS_ATTENTION_STATUSES = [
    AWAITING_REVIEW,
    MORE_DATA_NEEDED,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
]

LOWER_THRESHOLD = settings.AVL_LOWER_THRESHOLD
UPPER_THRESHOLD = 0.7

AVL_API_STATUS_MAP = {
    "live": AVLFeedStatus.live.value,
    "inactive": AVLFeedStatus.inactive.value,
    "error": AVLFeedStatus.error.value,
}


AVL_GRANULARITY_WEEKLY = "weekly"
AVL_GRANULARITY_DAILY = "daily"
