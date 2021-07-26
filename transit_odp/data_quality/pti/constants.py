from django.conf import settings
from django.template.defaultfilters import date

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


IMPORTANT_NOTE = (
    "Data containing this observation will be rejected by "
    f'BODS after {date(settings.PTI_ENFORCED_DATE, "jS F, Y")}'
)
REF_URL = settings.PTI_PDF_URL
REF_PREFIX = "Please refer to section "
REF_SUFFIX = " in the BODS PTI profile v1.1 document: "
NO_REF = "Please refer to the BODS PTI profile v1.1 document: "
