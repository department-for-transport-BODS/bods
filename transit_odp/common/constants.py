from django.utils.translation import gettext_lazy as _
from enum import Enum

DEFAULT_ERROR_SUMMARY = _("There is a problem")
TRUE = "True"
FALSE = "False"

UTF8 = "utf-8"


class CSVFileName(Enum):
    DELETE_DATASETS = "delete_datasets.csv"
    RERUN_ETL_TIMETABLES = "rerun_timetables_etl.csv"
    RERUN_FARES_VALIDATION = "rerun_fares_validator.csv"
