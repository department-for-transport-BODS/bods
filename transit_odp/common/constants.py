from enum import Enum

from django.utils.translation import gettext_lazy as _

DEFAULT_ERROR_SUMMARY = _("There is a problem")
TRUE = "True"
FALSE = "False"

UTF8 = "utf-8"

ACCESSIBILITY_REPORT_FILE_NAME = (
    "BODS_Accessibility_VPAT_2.4_WCAG_2.2_Edition_v0.1.docx"
)


class CSVFileName(Enum):
    DELETE_DATASETS = "delete_datasets.csv"
    RERUN_ETL_TIMETABLES = "rerun_timetables_etl.csv"
    RERUN_DQS_TIMETABLES = "rerun_timetables_dqs.csv"
    RERUN_FARES_VALIDATION = "rerun_fares_validator.csv"
