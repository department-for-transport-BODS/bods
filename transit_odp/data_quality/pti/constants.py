from django.conf import settings
from django.template.defaultfilters import date
from django.utils import timezone

OPERATION_DAYS = ("DaysOfOperation", "DaysOfNonOperation")

# holidays common for english and scottish

BANK_HOLIDAYS_COMMON = [
    "ChristmasEve",
    "ChristmasDay",
    "ChristmasDayHoliday",
    "BoxingDay",
    "BoxingDayHoliday",
    "NewYearsDay",
    "NewYearsDayHoliday",
    "GoodFriday",
    "EasterMonday",
    "SpringBank",
    "MayDay",
]

# holidays only for english regions
BANK_HOLIDAYS_ONLY_ENGLISH = [
    "NewYearsEve",
    "LateSummerBankHolidayNotScotland",
]

# holidays only for scottish regions
BANK_HOLIDAYS_ONLY_SCOTTISH = [
    "StAndrewsDayHoliday",
    "Jan2ndScotland",
    "Jan2ndScotlandHoliday",
]

BANK_HOLIDAYS = BANK_HOLIDAYS_COMMON + BANK_HOLIDAYS_ONLY_ENGLISH
SCOTTISH_BANK_HOLIDAYS = BANK_HOLIDAYS_COMMON + BANK_HOLIDAYS_ONLY_SCOTTISH
OTHER_PUBLIC_HOLIDAYS = ["OtherPublicHoliday"]

# old holidays, which may not come now
OLD_HOLIDAYS_ALREADY_REMOVED = [
    "StAndrewsDay",
    "AugustBankHolidayScotland",
]


def get_important_note():
    pti_enforced_date = settings.PTI_ENFORCED_DATE
    if pti_enforced_date.date() > timezone.localdate():
        important_note = (
            "Data containing this observation will be rejected by "
            f'BODS after {date(pti_enforced_date, "jS F, Y")}'
        )
    else:
        important_note = ""

    return important_note


REF_URL = settings.PTI_PDF_URL
REF_PREFIX = "Please refer to section "
REF_SUFFIX = " in the BODS PTI profile v1.1 document: "
NO_REF = "Please refer to the BODS PTI profile v1.1 document: "

FLEXIBLE_SERVICE = "FlexibleService"
STANDARD_SERVICE = "StandardService"
MODE_COACH = "coach"
