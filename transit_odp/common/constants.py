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
    FARES_REQUIRE_ATTENTION = "is_fares_require_attention_active"
    COMPLETE_SERVICE_PAGES = "is_complete_service_pages_active"
    AVL_REQUIRES_ATTENTION = "is_avl_require_attention_active"
    OPERATOR_PREFETCH_SRA = "is_operator_prefetch_sra_active"
    UILTA_PREFETCH_SRA = "is_uilta_prefetch_sra_active"
    CANCELLATION_LOGIC = "is_cancellation_logic_active"
    COMPLETE_SERVICE_PAGES_REAL_TIME_DATA = (
        "is_complete_service_pages_real_time_data_active"
    )
    PREFETCH_DATABASE_COMPLIANCE_REPORT = "is_prefetch_db_compliance_report_active"

    # Report Flags are different from the portal flags
    # Reason: Reports are processed in the background, slowness won't be an issue for
    # compliance report, also these values from report will be consumed in ABODS
    DQS_REQUIRE_ATTENTION_COMPLIANCE_REPORT = (
        "dqs_require_attention_compliance_report_active"
    )
    FARES_REQUIRE_ATTENTION_COMPLIANCE_REPORT = (
        "is_fares_require_attention_compliance_report_active"
    )
    FRANCHISE_ORGANISATION = "is_franchise_organisation_active"
    CREATE_SEVEN_DAY_PPC_REPROT_DAILY = "is_create_seven_day_ppc_report_daily"
    OPERATOR_PREFETCH_SRA_FROM_DB = "is_operator_prefetch_sra_from_db_active"
    UILTA_PREFETCH_SRA_FROM_DB = "is_uilta_prefetch_sra_from_db_active"
