from enum import Enum

from django.utils.translation import gettext_lazy as _

DEFAULT_ERROR_SUMMARY = _("There is a problem")
TRUE = "True"
FALSE = "False"

UTF8 = "utf-8"


class CSVFileName(Enum):
    DELETE_DATASETS = "delete_datasets.csv"
    RERUN_ETL_TIMETABLES = "rerun_timetables_etl.csv"
    RERUN_DQS_TIMETABLES = "rerun_timetables_dqs.csv"
    RERUN_FARES_VALIDATION = "rerun_fares_validator.csv"


class FeatureFlags(Enum):
    DQS_REQUIRE_ATTENTION = "dqs_require_attention"
    FARES_REQUIRE_ATTENTION = "is_fares_require_attention"
    COMPLETE_SERVICE_PAGES = "is_complete_service_pages_active"
    AVL_REQUIRES_ATTENTION = "is_avl_require_attention_active"
