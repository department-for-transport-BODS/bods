from django.conf import settings

UNDERGOING = "Undergoing validation"
PARTIALLY_COMPLIANT = "Partially compliant"
AWAITING_REVIEW = "Awaiting publisher review"
COMPLIANT = "Compliant"
NON_COMPLIANT = "Non-compliant"
MORE_DATA_NEEDED = "Unavailable due to dormant feed"

LOWER_THRESHOLD = settings.AVL_LOWER_THRESHOLD
UPPER_THRESHOLD = 0.7
