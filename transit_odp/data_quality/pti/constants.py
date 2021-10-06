from django.conf import settings
from django.template.defaultfilters import date
from django.utils import timezone

OPERATION_DAYS = ("DaysOfOperation", "DaysOfNonOperation")
BANK_HOLIDAYS = [
    "ChristmasEve",
    "NewYearsEve",
    "ChristmasDay",
    "ChristmasDayHoliday",
    "BoxingDay",
    "BoxingDayHoliday",
    "NewYearsDay",
    "NewYearsDayHoliday",
    "GoodFriday",
    "EasterMonday",
    "MayDay",
    "SpringBank",
    "LateSummerBankHolidayNotScotland",
]
SCOTTISH_BANK_HOLIDAYS = [
    "StAndrewsDay",
    "StAndrewsDayHoliday",
    "Jan2ndScotland",
    "Jan2ndScotlandHoliday",
    "AugustBankHolidayScotland",
]
OTHER_PUBLIC_HOLIDAYS = ["OtherPublicHoliday"]


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
