import logging
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd
from django.db.models import Q, Subquery
from django.utils.timezone import now
from waffle import flag_is_active

from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.common.constants import FeatureFlags
from transit_odp.dqs.constants import Level
from transit_odp.dqs.models import ObservationResults, TaskResults
from transit_odp.fares.models import DataCatalogueMetaData
from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import INACTIVE
from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.organisation.models.organisations import ConsumerFeedback, Licence
from transit_odp.otc.constants import CANCELLED_SERVICE_STATUS
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.constants import FARES_STALENESS_STATUS
from transit_odp.transmodel.models import Service as TransmodelService
from transit_odp.transmodel.models import ServicePatternStop

logger = logging.getLogger(__name__)
DQS_SRA_PREFIX = "DQS-SRA-PREFIX"


def get_line_level_in_scope_otc_map(organisation_id: int) -> Dict[tuple, OTCService]:
    """
    Get a dictionary which includes all line level Services for an organisation.
    excluding exempted services and Out of Season seasonal services.

    Args:
        organisation_id (int): Organisation id

    Returns:
        Dict[tuple, OTCService]: List of Services
    """
    return {
        (
            f"{service.registration_number.replace('/', ':')}",
            f"{split_service_number}",
        ): service
        for service in OTCService.objects.get_otc_data_for_organisation(organisation_id)
        for split_service_number in service.service_number.split("|")
    }


def get_all_line_level_otc_map(organisation_id: int) -> Dict[tuple, OTCService]:
    """
    Get a dictionary which includes all line level Services for an organisation.

    Args:
        organisation_id (int): Organisation id

    Returns:
        Dict[tuple, OTCService]: List of Services
    """
    return {
        (
            f"{service.registration_number.replace('/', ':')}",
            f"{split_service_number}",
        ): service
        for service in OTCService.objects.get_all_otc_data_for_organisation(
            organisation_id
        )
        for split_service_number in service.service_number.split("|")
    }


def get_otc_map_lta(lta_list) -> Dict[str, OTCService]:
    """
    Get a list of dictionaries which includes all OTC Services for a LTA,
    excluding exempted services and Out of Season seasonal services.
    """
    otc_data_lta_queryset = OTCService.objects.get_otc_data_for_lta(lta_list)
    if otc_data_lta_queryset is not None:
        return {
            service.registration_number.replace("/", ":"): service
            for service in otc_data_lta_queryset
        }
    else:
        return {}


def get_line_level_otc_map_lta(lta_list) -> Dict[tuple, OTCService]:
    """
    Get a mapping of line-level OTC (Office of Transport Commissioner)
    services for each LTA (Local Transport Authority).

    This function fetches all OTC services for the given list of
    Local Authorities, excluding exempted services and out-of-season
    seasonal services. It returns a dictionary where the keys are
    tuples composed of split service numbers and modified registration
    numbers, and the values are the corresponding OTCService instances.

    Args:
        lta_list (list[LocalAuthority]): A list of Local Authority objects
                                         to filter the services.

    Returns:
        Dict[tuple, OTCService]
    """
    otc_data_lta_queryset = OTCService.objects.get_otc_data_for_lta(lta_list)
    if otc_data_lta_queryset is not None:
        return {
            (
                f"{split_service_number}",
                f"{service.registration_number.replace('/', ':')}",
            ): service
            for service in otc_data_lta_queryset
            for split_service_number in service.service_number.split("|")
        }
    else:
        return {}


def get_txc_map(org_id: int) -> Dict[str, TXCFileAttributes]:
    """
    Get a list of dictionaries of live TXCFileAttributes for an organisation
    with relevant effective staleness dates annotated.
    """
    return {
        txcfa.service_code: txcfa
        for txcfa in TXCFileAttributes.objects.filter(
            revision__dataset__organisation_id=org_id
        )
        .get_active_live_revisions()
        .add_staleness_dates()
        .order_by(
            "service_code",
            "-revision__published_at",
            "-revision_number",
            "-modification_datetime",
            "-operating_period_start_date",
            "-filename",
        )
        .distinct("service_code")
    }


def get_line_level_txc_map_lta(lta_list) -> Dict[tuple, TXCFileAttributes]:
    """
    Get a dictionary of live TXCFileAttributes for each LTA (Local Transport
    Authority) with relevant effective staleness dates annotated.

    This function retrieves all live TXCFileAttributes for the given list of
    Local Authorities. It includes annotations for effective staleness dates
    and returns a dictionary where the keys are tuples of line names and service
    codes, and the values are the corresponding TXCFileAttributes instances.

    Args:
        lta_list (list[LocalAuthority]): A list of Local Authority objects to
                                         filter the services.

    Returns:
        Dict[tuple, TXCFileAttributes]
    """
    line_level_txc_map = {}
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if len(lta_list) > 0:
        weca_services_list = OTCService.objects.filter(
            atco_code__in=AdminArea.objects.filter(ui_lta=lta_list[0].ui_lta).values(
                "atco_code"
            ),
            licence_id__isnull=False,
        ).values("id")

        if weca_services_list:
            services_subquery_list.append(weca_services_list)

    if services_subquery_list:
        final_subquery = None
        for service_queryset in services_subquery_list:
            if final_subquery is None:
                final_subquery = service_queryset
            else:
                final_subquery = final_subquery | service_queryset
        final_subquery = final_subquery.distinct()

        service_code_subquery = Subquery(
            OTCService.objects.filter(id__in=Subquery(final_subquery.values("id")))
            .add_service_code()
            .values("service_code")
        )

        txc_file_attributes = (
            TXCFileAttributes.objects.filter(service_code__in=service_code_subquery)
            .get_active_live_revisions()
            .add_staleness_dates()
            .add_split_linenames()
            .add_organisation_name()
            .add_is_null_operating_period_end()
            .order_by(
                "service_code",
                "-revision__published_at",
                "-revision_number",
                "-is_null_operating_period_end",
                "-operating_period_end_date",
                "-modification_datetime",
                "-operating_period_start_date",
                "-filename",
            )
        )

        for txc_attribute in txc_file_attributes:
            key = (txc_attribute.line_name_unnested, txc_attribute.service_code)
            if key not in line_level_txc_map:
                line_level_txc_map[key] = txc_attribute
        return line_level_txc_map

    else:
        return {}


def get_line_level_txc_map(org_id: int) -> Dict[tuple, TXCFileAttributes]:
    """
    Get a list of dictionaries of live TXCFileAttributes for an organisation
    with relevant effective staleness dates annotated.
    """
    line_level_txc_map = {}

    txc_file_attributes = (
        TXCFileAttributes.objects.filter(revision__dataset__organisation_id=org_id)
        .get_active_live_revisions()
        .add_staleness_dates()
        .add_split_linenames()
        .add_organisation_name()
        .order_by(
            "service_code",
            "line_name_unnested",
            "-revision__published_at",
            "-revision_number",
            "-modification_datetime",
            "-operating_period_start_date",
            "-filename",
        )
        .distinct("service_code", "line_name_unnested")
    )

    for txc_file in txc_file_attributes:
        key = (txc_file.service_code, txc_file.line_name_unnested)
        if key not in line_level_txc_map:
            line_level_txc_map[key] = txc_file
    return line_level_txc_map


def get_line_level_txc_map_service_base(
    service_codes: List,
) -> Dict[tuple, TXCFileAttributes]:
    """
    Get a list of dictionaries of live TXCFileAttributes for an organisation
    with relevant effective staleness dates annotated.
    """
    line_level_txc_map = {}

    txc_file_attributes = (
        TXCFileAttributes.objects.filter(service_code__in=service_codes)
        .get_active_live_revisions()
        .add_staleness_dates()
        .add_split_linenames()
        .add_organisation_name()
        .add_is_null_operating_period_end()
        .order_by(
            "service_code",
            "line_name_unnested",
            "-revision__published_at",
            "-revision_number",
            "-is_null_operating_period_end",
            "-operating_period_end_date",
            "-modification_datetime",
            "-operating_period_start_date",
            "-filename",
        )
        .distinct("service_code", "line_name_unnested")
    )

    for txc_file in txc_file_attributes:
        key = (txc_file.service_code, txc_file.line_name_unnested)
        if key not in line_level_txc_map:
            line_level_txc_map[key] = txc_file

    return line_level_txc_map


def get_txc_map_lta(lta_list) -> Dict[str, TXCFileAttributes]:
    """
    Get a list of dictionaries of live TXCFileAttributes for a LTA
    with relevant effective staleness dates annotated.
    """
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if len(lta_list) > 0:
        weca_services_list = OTCService.objects.filter(
            atco_code__in=AdminArea.objects.filter(ui_lta=lta_list[0].ui_lta).values(
                "atco_code"
            ),
            licence_id__isnull=False,
        ).values("id")

        if weca_services_list:
            services_subquery_list.append(weca_services_list)

    if services_subquery_list:
        final_subquery = None
        for service_queryset in services_subquery_list:
            if final_subquery is None:
                final_subquery = service_queryset
            else:
                final_subquery = final_subquery | service_queryset
        final_subquery = final_subquery.distinct()

        service_code_subquery = Subquery(
            OTCService.objects.filter(id__in=Subquery(final_subquery.values("id")))
            .add_service_code()
            .values("service_code")
        )
        return {
            txcfa.service_code: txcfa
            for txcfa in TXCFileAttributes.objects.filter(
                service_code__in=service_code_subquery
            )
            .get_active_live_revisions()
            .add_staleness_dates()
            .add_organisation_name()
            .order_by(
                "service_code",
                "-revision__published_at",
                "-revision_number",
                "-modification_datetime",
                "-operating_period_start_date",
                "-filename",
            )
            .distinct("service_code")
        }
    else:
        return {}


def _update_data(
    object_list: List[Dict[str, str]],
    service: OTCService,
    line_number: Optional[str] = None,
) -> None:
    """
    Append data to object_list of services requiring attention.
    """

    object_list.append(
        {
            "licence_number": service.otc_licence_number,
            "service_code": service.registration_number,
            "line_number": line_number if line_number else service.service_number,
        }
    )


def evaluate_staleness(service: OTCService, file_attribute: TXCFileAttributes) -> tuple:
    """
    Checks key staleness dates on live TXCFileAttributes and OTC Service to determine
    if a service is Stale and returns all Stale live services.

    Staleness logic:
        Staleness Status - Up to Date:
            Default status for service codes published to BODS
        Staleness Status - Stale - OTC Variation:
            Staleness Status - Stale - OTC Variation
            When Associated data is No
            AND
            today >= Effective stale date due to OTC effective date
            NB: Associated data is Yes IF
            (last modified date >= Association date due to OTC effective date
            OR Operating period start date = OTC effective date).
        Staleness Status - Stale - 42 Day Look Ahead:
            If Operating period end date is present
            AND
            Staleness status is not OTC Variation
            AND
            Operating period end date < today + 42 days
            AND
            if Service End Date is present
            And
            Operating period end date < Service End Date
        Staleness Status - Stale - 12 months old:
            If Staleness status is not OTC Variation
            AND
            Staleness status is not 42 day look ahead
            AND
            last_modified + 365 days <= today
    """
    is_cancellation_logic_active = flag_is_active(
        "", FeatureFlags.CANCELLATION_LOGIC.value
    )
    today = now().date()
    last_modified = file_attribute.modification_datetime.date()
    effective_date = service.effective_date
    effective_stale_date_otc_effective_date = (
        service.effective_stale_date_otc_effective_date
    )
    # Service Effective date - 70 days
    association_date_otc_effective_date = service.association_date_otc_effective_date
    operating_period_start_date = file_attribute.operating_period_start_date
    operating_period_end_date = file_attribute.operating_period_end_date
    expiry_date = service.end_date
    forty_two_days_from_today = today + timedelta(days=42)

    is_data_associated = (
        last_modified >= association_date_otc_effective_date
        or operating_period_start_date == effective_date
    )

    staleness_otc = (
        not is_data_associated
        if today >= effective_stale_date_otc_effective_date
        else False
    )

    if is_cancellation_logic_active:
        if expiry_date is None:
            expiry_date = forty_two_days_from_today

        least_date = (
            expiry_date - timedelta(days=1)
            if expiry_date < forty_two_days_from_today
            else forty_two_days_from_today
        )

        if service.registration_status in CANCELLED_SERVICE_STATUS:
            staleness_otc = False
            if least_date > service.effective_date:
                least_date = service.effective_date - timedelta(days=1)

        is_operating_period_lt_forty_two_days = (
            operating_period_end_date and operating_period_end_date < least_date
            if operating_period_end_date
            else False
        )

        staleness_42_day_look_ahead = (
            not staleness_otc and is_operating_period_lt_forty_two_days
        )
    else:
        staleness_42_day_look_ahead = (
            (
                not staleness_otc
                and operating_period_end_date < forty_two_days_from_today
            )
            if operating_period_end_date
            else False
        )

    staleness_12_months_old = (
        True
        if not staleness_42_day_look_ahead
        and not staleness_otc
        and (last_modified + timedelta(days=365) <= today)
        else False
    )

    return (
        staleness_42_day_look_ahead,
        staleness_12_months_old,
        staleness_otc,
    )


def is_stale(service: OTCService, file_attribute: TXCFileAttributes) -> bool:
    """
    Determines if a timetables service has any stale values that are True.

    Args:
        service (OTCService): OTC Service
        file_attribute (TXCFileAttributes): File attributes from TXC files

    Returns:
        bool: True or False if there is a stale value present.
    """
    return any(evaluate_staleness(service, file_attribute))


def evaluate_fares_staleness(
    operating_period_end_date: date, last_updated_date: date
) -> tuple:
    """
    Checks timeliness status for fares data.

    Fares Staleness logic:
        Staleness Status - Stale - 42 day look ahead is incomplete:
            If Operating period end date is present
            AND
            Operating period end date < today + 42 days
        Staleness Status - Stale - One year old:
            If last_modified + 365 days <= today

    Args:
        operating_period_end_date (date): Valid to date
        last_updated (date): Last updated date

    Returns:
        tuple: Boolean value for each staleness status
    """
    today = now().date()
    forty_two_days_from_today = today + timedelta(days=42)
    twelve_months_from_last_updated = last_updated_date + timedelta(days=365)

    if isinstance(operating_period_end_date, pd.Timestamp):
        operating_period_end_date = operating_period_end_date.date()
    if isinstance(last_updated_date, pd.Timestamp):
        last_updated_date = last_updated_date.date()
    if isinstance(twelve_months_from_last_updated, pd.Timestamp):
        twelve_months_from_last_updated = twelve_months_from_last_updated.date()

    staleness_42_day_look_ahead = (
        True
        if not pd.isna(operating_period_end_date)
        and (operating_period_end_date < forty_two_days_from_today)
        else False
    )
    staleness_12_months_old = (
        True if (twelve_months_from_last_updated <= today) else False
    )

    return (
        staleness_42_day_look_ahead,
        staleness_12_months_old,
    )


def is_fares_stale(operating_period_end_date: date, last_updated: date) -> bool:
    """
    Determines if a fares service has any stale values that are True.

    Args:
        operating_period_end_date (date): Valid to value
        last_updated (date): Last update date

    Returns:
        bool: True or False if there is a stale value.
    """
    return any(evaluate_fares_staleness(operating_period_end_date, last_updated))


def get_fares_published_status(fares_dataset_id: int) -> str:
    """
    Returns value for 'Fares Published Status' column based on
    the presence of a dataset ID for a published fares dataset.

    Args:
        fares_dataset_id (int): Fares Dataset ID

    Returns:
        str: Published or Unpublished for 'Fares Published Status' column
    """
    if not pd.isna(fares_dataset_id):
        return "Published"
    return "Unpublished"


def get_fares_timeliness_status(valid_to: date, last_updated_date: date) -> str:
    """
    Returns value for 'Fares Timeliness Status' column based on the following logic:
        12 months old:
            If 'Last updated' + 1 year <= today's date
            then timeliness status = 'One year old'
        42 day look ahead:
            If NETEX:Operating Period End Date (valid to) < today + 42 days
            then timeliness status = '42 day look ahead is incomplete'
        Else Not Stale

    Args:
        operating_period_end_date (date): Valid to value
        last_updated (date): Last update date

    Returns:
        str: Status value for 'Fares Timeliness Status' column
    """
    fares_staleness_status = "Not Stale"
    if (not pd.isna(last_updated_date)) and (not pd.isna(valid_to)):
        if is_fares_stale(valid_to, last_updated_date):
            fares_rad = evaluate_fares_staleness(valid_to, last_updated_date)
            fares_staleness_status = FARES_STALENESS_STATUS[fares_rad.index(True)]

    return fares_staleness_status


def get_fares_compliance_status(is_fares_compliant: bool) -> str:
    """
    Returns value for 'Fares Compliance Status' column based on the
    compliance of the fares data published to BODS.

    Args:
        is_fares_compliant (bool): BODS compliance

    Returns:
        str: Yes or No for 'Fares Compliance Status' column
    """
    if not pd.isna(is_fares_compliant) and is_fares_compliant:
        return "Yes"
    return "No"


def get_fares_requires_attention(
    fares_published_status: str,
    fares_timeliness_status: str,
    fares_compliance_status: str,
) -> str:
    """
    Returns value for 'Fares requires attention' column based on the following logic:
        If 'Fares Published Status' equal to Published
        AND 'Fares Timeliness Status' equal to Not Stale
        AND 'Fares Compliance Status' equal to Yes
        then 'Fares requires attention' = No.
        Else
        the 'Fares requires attention' = Yes.

    Args:
        fares_published_status (str): Value of 'Fares Published Status'
        fares_timeliness_status (str): Value of 'Fares Timeliness Status'
        fares_compliance_status (str): Value of 'Fares Compliance Status'

    Returns:
        str: Yes or No for 'Fares requires attention' column
    """
    if (
        (fares_published_status == "Published")
        and (fares_timeliness_status == "Not Stale")
        and (fares_compliance_status == "Yes")
    ):
        return "No"
    return "Yes"


def get_requires_attention_line_level_data(org_id: int) -> List[Dict[str, str]]:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. not live
    in BODS at all, or live but meeting new Staleness conditions.

    Returns list of objects of each service requiring attention for an organisation.
    """
    object_list = []
    dqs_critical_issues_service_line_map = []
    otc_map = get_line_level_in_scope_otc_map(org_id)
    service_codes = [service_code for (service_code, line_name) in otc_map]
    txcfa_map = get_line_level_txc_map_service_base(service_codes)
    is_dqs_require_attention = flag_is_active(
        "", FeatureFlags.DQS_REQUIRE_ATTENTION.value
    )
    if is_dqs_require_attention:
        dqs_critical_issues_service_line_map = get_dq_critical_observation_services_map(
            txcfa_map
        )

    for service_key, service in otc_map.items():
        file_attribute = txcfa_map.get(service_key)
        if file_attribute is None:
            _update_data(object_list, service, service_key[1])
        elif is_stale(service, file_attribute) or (
            is_dqs_require_attention
            and service_key in dqs_critical_issues_service_line_map
        ):
            _update_data(object_list, service, service_key[1])
    return object_list


def is_avl_requires_attention(
    noc: str,
    line_name: str,
    synced_in_last_month: bool,
    uncounted_activity_df: pd.DataFrame,
):
    """Return True if the avl service requires the attention, otherwise False"""

    if not noc or (
        not uncounted_activity_df.loc[
            (uncounted_activity_df["OperatorRef"] == noc)
            & (
                uncounted_activity_df["LineRef"].isin(
                    [line_name, line_name.replace(" ", "_")]
                )
            )
        ].empty
        or f"{line_name}__{noc}" not in synced_in_last_month
    ):
        return True

    return False


def get_avl_requires_attention_line_level_data(
    org_id: int,
    uncounted_activity_df: pd.DataFrame = None,
    synced_in_last_month: List = None,
) -> List[Dict[str, str]]:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. service has
    been published for a service or has a matching issue.

    Returns list of objects of each service requiring attention for an organisation.
    """
    is_avl_require_attention_active = flag_is_active(
        "", "is_avl_require_attention_active"
    )
    if not is_avl_require_attention_active:
        return []
    otc_map = get_line_level_in_scope_otc_map(org_id)
    service_codes = [service_code for (service_code, line_name) in otc_map]
    txcfa_map = get_line_level_txc_map_service_base(service_codes)

    if uncounted_activity_df is None or synced_in_last_month is None:
        uncounted_activity_df = get_vehicle_activity_operatorref_linename()
        abods_registry = AbodsRegistery()
        synced_in_last_month = abods_registry.records()

    object_list = []
    for service_key, service in otc_map.items():
        file_attribute = txcfa_map.get(service_key)
        noc = file_attribute.national_operator_code if file_attribute else None
        line_name = service_key[1]

        if is_avl_requires_attention(
            noc, line_name, synced_in_last_month, uncounted_activity_df
        ):
            _update_data(object_list, service, line_name)

    logging.info(f"AVL-REQUIRE-ATTENTION: total objects {len(object_list)}")
    return object_list


def get_requires_attention_data_lta(lta_list: List) -> int:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. not live
    in BODS at all, or live but meeting new Staleness conditions.

    Returns list of objects of each service requiring attention for a LTA.
    """
    object_list = []
    lta_services_requiring_attention = 0
    otc_map = get_otc_map_lta(lta_list)
    txcfa_map = get_txc_map_lta(lta_list)
    for service_code, service in otc_map.items():
        file_attribute = txcfa_map.get(service_code)
        if file_attribute is None:
            _update_data(object_list, service)
        elif is_stale(service, file_attribute):
            _update_data(object_list, service)
    lta_services_requiring_attention = len(object_list)

    return lta_services_requiring_attention


def get_timetable_records_require_attention_lta_line_level_length(
    lta_list: List,
) -> int:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. service has
    been published for a service or has a matching issue.

    Returns list of objects of each service requiring attention for an organisation.
    """
    object_list = []
    dqs_critical_issues_service_line_map = []
    timetables_lta_services_requiring_attention = 0
    otc_map = get_line_level_otc_map_lta(lta_list)
    txcfa_map = get_line_level_txc_map_lta(lta_list)
    is_dqs_require_attention = flag_is_active(
        "", FeatureFlags.DQS_REQUIRE_ATTENTION.value
    )
    if is_dqs_require_attention:
        dqs_critical_issues_service_line_map = get_dq_critical_observation_services_map(
            txcfa_map
        )
    for (service_number, registration_number), service in otc_map.items():
        file_attribute = txcfa_map.get((service_number, registration_number))
        if file_attribute is None:
            _update_data(object_list, service, line_number=service_number)
        elif is_stale(service, file_attribute) or (
            is_dqs_require_attention
            and (registration_number, service_number)
            in dqs_critical_issues_service_line_map
        ):
            _update_data(object_list, service, line_number=service_number)
    timetables_lta_services_requiring_attention = len(object_list)
    return timetables_lta_services_requiring_attention


def get_avl_records_require_attention_lta_line_level_objects(
    lta_list: List,
    uncounted_activity_df: pd.DataFrame = None,
    synced_in_last_month: List = None,
) -> int:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. service has
    been published for a service or has a matching issue.

    Returns list of objects of each service requiring attention for an organisation.
    """
    object_list = []
    otc_map = get_line_level_otc_map_lta(lta_list)
    txcfa_map = get_line_level_txc_map_lta(lta_list)
    if uncounted_activity_df is None or synced_in_last_month is None:
        uncounted_activity_df = get_vehicle_activity_operatorref_linename()
        abods_registry = AbodsRegistery()
        synced_in_last_month = abods_registry.records()

    for service_key, service in otc_map.items():
        file_attribute = txcfa_map.get(service_key)
        if file_attribute is not None:
            operator_ref = file_attribute.national_operator_code
            line_name = service_key[0]
            if (
                not uncounted_activity_df.loc[
                    (uncounted_activity_df["OperatorRef"] == operator_ref)
                    & (
                        uncounted_activity_df["LineRef"].isin(
                            [line_name, line_name.replace(" ", "_")]
                        )
                    )
                ].empty
                or f"{line_name}__{operator_ref}" not in synced_in_last_month
            ):
                _update_data(object_list, service, line_name)
        else:
            _update_data(object_list, service, service_key[0])
    return object_list


def get_avl_records_require_attention_lta_line_level_length(
    lta_list: List,
    uncounted_activity_df: pd.DataFrame = None,
    synced_in_last_month: List = None,
) -> int:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. service has
    been published for a service or has a matching issue.

    Returns the length of objects.
    """
    return len(
        get_avl_records_require_attention_lta_line_level_objects(
            lta_list, uncounted_activity_df, synced_in_last_month
        )
    )


def get_fares_records_require_attention_lta_line_level_objects(lta_list: List) -> List:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list and Fares list to determine which OTC Services require attention, i.e., those
    not Published in Fares at all  but meeting new staleness conditions.

    This function identifies services that require attention based on their status in
    BODS. It compares the OTC services with the TXCFileAttributes and Fares and updates a list
    of services requiring attention if they are not live or are considered stale.
    The length of this list is returned as the result.

    Args:
        lta_list (list): A list of Local Authority objects to filter the services.

    Returns:
        List: The objects of services requiring attention.
    """
    object_list = []
    otc_map = get_line_level_otc_map_lta(lta_list)
    txcfa_map = get_line_level_txc_map_lta(lta_list)
    fares_df = get_fares_dataset_map(txcfa_map)

    for service_key, service in otc_map.items():

        file_attribute = txcfa_map.get(service_key)
        # If no file attribute (TxcFileAttribute), service requires attention
        if file_attribute is None:
            _update_data(object_list, service, service_key[0])
        elif fares_df.empty:
            _update_data(object_list, service, service_key[0])
        else:
            fra = FaresRequiresAttention(None)
            if fra.is_fares_requires_attention(file_attribute, fares_df):
                line_name = file_attribute.line_name_unnested
                _update_data(object_list, service, line_name)
    return object_list


def get_fares_records_require_attention_lta_line_level_length(lta_list: List) -> int:
    """
    Get the count of services require attention for lta
    Args:
        lta_list (list): A list of Local Authority objects to filter the services.

    Returns:
        int: The count of services requiring attention.
    """
    return len(get_fares_records_require_attention_lta_line_level_objects(lta_list))


def get_requires_attention_data_lta_line_level_objects(lta_list: List) -> List:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention, i.e., those
    not live in BODS (Bus Open Data Service) at all, or live but meeting new
    staleness conditions.

    This function identifies services that require attention based on their status in
    BODS. It compares the OTC services with the TXCFileAttributes and updates a list
    of services requiring attention if they are not live or are considered stale.
    The length of this list is returned as the result.

    Args:
        lta_list (list): A list of Local Authority objects to filter the services.

    Returns:
        List: The objects of services requiring attention.
    """
    object_list = []
    dqs_critical_issues_service_line_map = []
    otc_map = get_line_level_otc_map_lta(lta_list)
    txcfa_map = get_line_level_txc_map_lta(lta_list)
    is_dqs_require_attention = flag_is_active(
        "", FeatureFlags.DQS_REQUIRE_ATTENTION.value
    )
    if is_dqs_require_attention:
        dqs_critical_issues_service_line_map = get_dq_critical_observation_services_map(
            txcfa_map
        )
    for (service_number, registration_number), service in otc_map.items():
        file_attribute = txcfa_map.get((service_number, registration_number))
        if file_attribute is None:
            _update_data(object_list, service, line_number=service_number)
        elif is_stale(service, file_attribute) or (
            is_dqs_require_attention
            and (registration_number, service_number)
            in dqs_critical_issues_service_line_map
        ):
            _update_data(object_list, service, line_number=service_number)
    return object_list


def get_requires_attention_data_lta_line_level_length(lta_list: List) -> int:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention, i.e., those
    not live in BODS (Bus Open Data Service) at all, or live but meeting new
    staleness conditions.

    This function identifies services that require attention based on their status in
    BODS. It compares the OTC services with the TXCFileAttributes and updates a list
    of services requiring attention if they are not live or are considered stale.
    The length of this list is returned as the result.

    Args:
        lta_list (list): A list of Local Authority objects to filter the services.

    Returns:
        int: The count of services requiring attention.
    """
    return len(get_requires_attention_data_lta_line_level_objects(lta_list))


def get_dq_critical_observation_services_map(
    txc_map: Dict[tuple, TXCFileAttributes]
) -> List[tuple]:
    """Check for data quality critical issue for service code
    and line name combination for the current revision only,
    Method will receive the txcfileattributes table dictionary

    Returns:
        dict[tuple, str]: return a list of services
    """
    txc_map_df = pd.DataFrame(
        [
            {
                "service_code": obj.service_code,
                "line_name_unnested": obj.line_name_unnested,
                "revision_id": obj.revision_id,
                "id": obj.id,
            }
            for _, obj in txc_map.items()
        ]
    )
    return get_dq_critical_observation_services_map_from_dataframe(txc_map_df)


def query_dq_critical_observation(query, revision_ids: list) -> List[tuple]:
    """Query for data quality critical issue for service code
    and line name combination for the current revision only,
    Using two scenarions, Any of the scenario with mark
    Dq require attention to True

    1. the Transmodel tables relations with dqs_observationresults
    Transmodel services -> Transmodel Service Patterns
    -> Transmodel Service Pattern Stops -> Dqs Observationresult

    And for checking the observation result must be critical
    Dqs Observationresult -> Taskresults -> checks

    2. Check for customer feedback present and not suppressed
    Transmodel service -> Organisation feedback

    Due to database restriction we can not use above given joins, we have to use
    Dataframe approch in order to acheive the desired values. Following steps will
    be followed

    1. Get dataframe to get service_patter_ids for the given query of registration number,
        line name, revision id
    2. Get dataframe by querying servicepatternstops table from the service_pattern_ids extracted
        in step 1
    3. Merge the dataframe built on step 1 and step 2 with left join
        (To prevent any service.id loss)
    4. Get the observations with ciritical type and merge the selected stop points with the
        Step 3 dataframe
    5. Now to get consumer feedback use the service_ids extracted on Step 1 df and search for
        feedbacks which are not suppressed
    6. Merge the dataframe of consumer feedbacks with main dataframe
    7. Return the registration number and line name for which any value (Observation with ciritical
        or Consumer feedback) is present

    Returns:
        dict[tuple, str]: return a list of services"""

    service_pattern_ids_df = get_service_patterns_df(query)
    if service_pattern_ids_df.empty:
        return []

    logger.info(
        "{} Found service patterns {}".format(
            DQS_SRA_PREFIX, len(list(service_pattern_ids_df["service_id"]))
        )
    )

    dqs_observation_df = get_dqs_observations_df(service_pattern_ids_df, revision_ids)
    logger.info(
        "{} Found service patterns stops {}".format(
            DQS_SRA_PREFIX, len(list(dqs_observation_df["service_pattern_stop_id"]))
        )
    )

    service_pattern_stops_df = get_service_pattern_stops_df(dqs_observation_df)
    logger.info(
        "{} Found service patterns from stops {}".format(
            DQS_SRA_PREFIX,
            len(list(service_pattern_stops_df["service_pattern_stop_id"])),
        )
    )

    if service_pattern_stops_df.empty:
        return []

    service_pattern_ids_df = service_pattern_stops_df.merge(
        service_pattern_ids_df, on=["service_pattern_id"], how="left"
    )

    dqs_require_attention_df = service_pattern_ids_df[["service_code", "line_name"]]
    logger.info("{} Returning the df".format(DQS_SRA_PREFIX))
    return list(dqs_require_attention_df.itertuples(index=False, name=None))


def get_dq_critical_observation_services_map_from_dataframe(
    txc_map: pd.DataFrame,
) -> List[tuple]:
    """Check for data quality critical issue for service code
    and line name combination for the current revision only,
    Method will receive a dataframe for the txc files

    Returns:
        dict[tuple, str]: return a list of services
    """
    if txc_map.empty:
        return []

    query = Q()
    revision_ids = []
    for _, row in txc_map.iterrows():
        revision_ids.append(row["revision_id"])
        query |= Q(
            service_code=row["service_code"],
            service_patterns__line_name=row["line_name_unnested"],
            revision_id=row["revision_id"],
            txcfileattributes_id=row["id"],
        )

    return query_dq_critical_observation(query, revision_ids)


def get_fares_dataset_map(txc_map: Dict[tuple, TXCFileAttributes]) -> pd.DataFrame:
    """Find fares data compatible to NOC and Line name

    Args:
        txc_map (Dict[tuple, TXCFileAttributes]): List of txc file attributes

    Returns:
        pd.DataFrame: DataFrame containing the fares files details
    """
    nocs_list = []
    noc_linename_dict = []
    for _, file_attribute in txc_map.items():
        nocs_list.append(file_attribute.national_operator_code)
        noc_linename_dict.append(
            {
                "national_operator_code": file_attribute.national_operator_code,
                "line_name": file_attribute.line_name_unnested,
            }
        )
    noc_df = pd.DataFrame.from_dict(noc_linename_dict)
    noc_df.drop_duplicates(inplace=True)
    nocs_list = list(set(nocs_list))
    qs = (
        DataCatalogueMetaData.objects.filter(national_operator_code__overlap=nocs_list)
        .add_revision_and_dataset()
        .get_live_revision_data()
        .exclude(fares_metadata_id__revision__status=INACTIVE)
        .add_published_date()
        .add_compliance_status()
        .add_operator_id()
        .add_is_null_valid_to()
        .values(
            "xml_file_name",
            "valid_from",
            "valid_to",
            "line_name",
            "id",
            "national_operator_code",
            "fares_metadata_id",
            "last_updated_date",
            "is_fares_compliant",
            "dataset_id",
            "tariff_basis",
            "product_name",
            "operator_id",
            "is_null_valid_to",
        )
    )
    fares_df = pd.DataFrame.from_records(qs)

    if fares_df.empty:
        return pd.DataFrame(
            columns=[
                "xml_file_name",
                "valid_from",
                "valid_to",
                "line_name",
                "id",
                "national_operator_code",
                "fares_metadata_id",
                "last_updated_date",
                "is_fares_compliant",
                "dataset_id",
                "tariff_basis",
                "product_name",
                "operator_id",
            ]
        )

    fares_df = fares_df.explode("line_name")
    fares_df = fares_df.explode("national_operator_code")

    fares_df_merged = pd.DataFrame.merge(
        fares_df,
        noc_df,
        on=["line_name", "national_operator_code"],
        how="inner",
        indicator=False,
    )

    fares_df_merged["valid_to"] = pd.to_datetime(
        fares_df_merged["valid_to"], errors="coerce"
    )
    fares_df_merged["valid_from"] = pd.to_datetime(
        fares_df_merged["valid_from"], errors="coerce"
    )

    fares_df_merged = (
        fares_df_merged.sort_values(
            by=["is_null_valid_to", "valid_to", "xml_file_name"],
            ascending=[False, False, False],
        )
        .drop_duplicates(subset=["line_name", "national_operator_code"])
        .reset_index()
    )

    return fares_df_merged


class FaresRequiresAttention:
    """
    Class to get the details of fares requiring attention
    """

    org_id: int

    def __init__(self, org_id):
        self._org_id = org_id

    def is_fares_requires_attention(
        self, txc_file: TXCFileAttributes, fares_df: pd.DataFrame
    ):
        """
        Return True if the fares requires attention, otherwise False
        """

        if txc_file is None:
            return True

        if fares_df.empty:
            return True

        noc = txc_file.national_operator_code
        line_name = txc_file.line_name_unnested
        df = fares_df[
            (fares_df.national_operator_code == noc) & (fares_df.line_name == line_name)
        ]

        if not df.empty:
            row = df.iloc[0].to_dict()
            valid_to = row.get("valid_to", None)
            last_modified_date = row.get("last_updated_date", None)
            valid_to = None if pd.isnull(valid_to) else valid_to.date()
            last_modified_date = (
                None if pd.isnull(last_modified_date) else last_modified_date.date()
            )

            fares_compliance_status = get_fares_compliance_status(
                row["is_fares_compliant"]
            )
            fares_timeliness_status = get_fares_timeliness_status(
                valid_to, last_modified_date
            )

            if (
                get_fares_requires_attention(
                    "Published", fares_timeliness_status, fares_compliance_status
                )
                == "No"
            ):
                return False

        return True

    def get_fares_requires_attention_line_level_data(self) -> List[Dict[str, str]]:
        """
        Compares an organisation's OTC Services dictionaries list with Fares Catalogue
        dictionaries list to determine which OTC Services require attention ie. not live
        in BODS at all, or live but meeting new Staleness conditions.

        Returns list of objects of each service requiring attention for an organisation.
        """
        object_list = []

        otc_map = get_line_level_in_scope_otc_map(self._org_id)
        service_codes = [service_code for (service_code, _) in otc_map]
        txcfa_map = get_line_level_txc_map_service_base(service_codes)
        fares_df = get_fares_dataset_map(txcfa_map)

        for service_key, service in otc_map.items():
            txc_file = txcfa_map.get(service_key)
            if self.is_fares_requires_attention(txc_file, fares_df):
                _update_data(object_list, service, service_key[1])

        return object_list


def get_service_patterns_df(query) -> pd.DataFrame:
    """Get list fo service pattern records for service pattern ids

    Args:
        query (_type_): Servie pattner filter (OR query)

    Returns:
        pd.DataFrame: Dataframe with list of transmodel service with service pattern id
    """
    service_pattern_ids_df = pd.DataFrame.from_records(
        TransmodelService.objects.filter(query).values(
            "id",
            "service_code",
            "service_patterns__line_name",
            "service_patterns__id",
            "txcfileattributes_id",
        )
    )
    if service_pattern_ids_df.empty:
        service_pattern_ids_df = pd.DataFrame(
            columns=[
                "id",
                "service_code",
                "service_patterns__line_name",
                "service_patterns__id",
                "txcfileattributes_id",
            ]
        )

    service_pattern_ids_df.rename(
        columns={
            "id": "service_id",
            "service_patterns__line_name": "line_name",
            "service_patterns__id": "service_pattern_id",
        },
        inplace=True,
    )
    return service_pattern_ids_df


def get_service_pattern_stops_via_sp_id_df(
    service_pattern_ids_df: pd.DataFrame,
) -> pd.DataFrame:
    """Get Service pattern stop ids for given service pattern ids

    Args:
        service_pattern_ids_df (pd.DataFrame): Dataframe with service pattern ids

    Returns:
        pd.DataFrame: Dataframe with service pattern stop ids
    """
    service_pattern_stops_qs = (
        ServicePatternStop.objects.filter(
            service_pattern_id__in=list(service_pattern_ids_df["service_pattern_id"])
        )
        .order_by()
        .values("id", "service_pattern_id")
    )

    service_pattern_stops_df = pd.DataFrame.from_records(service_pattern_stops_qs)
    if service_pattern_stops_df.empty:
        service_pattern_stops_df = pd.DataFrame(columns=["id", "service_pattern_id"])

    service_pattern_stops_df.rename(
        columns={"id": "service_pattern_stop_id"}, inplace=True
    )
    return service_pattern_stops_df


def get_service_pattern_stops_df(dqs_observation_df: pd.DataFrame) -> pd.DataFrame:
    """Get Service pattern stop ids for given service pattern ids

    Args:
        service_pattern_ids_df (pd.DataFrame): Dataframe with service pattern ids

    Returns:
        pd.DataFrame: Dataframe with service pattern stop ids
    """
    if dqs_observation_df.empty:
        pd.DataFrame(columns=["service_pattern_stop_id", "service_pattern_id"])

    service_pattern_stops_qs = (
        ServicePatternStop.objects.filter(
            id__in=list(dqs_observation_df["service_pattern_stop_id"])
        )
        .order_by()
        .values("id", "service_pattern_id")
    )

    service_pattern_stops_df = pd.DataFrame.from_records(service_pattern_stops_qs)
    if service_pattern_stops_df.empty:
        service_pattern_stops_df = pd.DataFrame(columns=["id", "service_pattern_id"])

    service_pattern_stops_df.rename(
        columns={"id": "service_pattern_stop_id"}, inplace=True
    )
    return service_pattern_stops_df


def get_dqs_observations_via_stops_df(
    service_pattern_stops_df: pd.DataFrame, revision_ids=List
) -> pd.DataFrame:
    """Get Critical DQS Observations for the given service pattern stops

    Args:
        service_pattern_stops_df (pd.DataFrame): service pattern stop ids

    Returns:
        pd.DataFrame: Dataframe with service pattern stops details
    """
    dqs_observation_df = pd.DataFrame(columns=["service_pattern_stop_id"])
    if not service_pattern_stops_df.empty:
        task_result_ids = TaskResults.objects.filter(
            dataquality_report__revision_id__in=revision_ids,
            checks__importance=Level.critical.value,
        ).values_list("id", flat=True)

        observation_result_qs = ObservationResults.objects.filter(
            service_pattern_stop_id__in=list(
                service_pattern_stops_df["service_pattern_stop_id"]
            ),
            taskresults_id__in=list(task_result_ids),
        ).values("service_pattern_stop_id")

        dqs_observation_df = pd.DataFrame.from_records(observation_result_qs)

        if dqs_observation_df.empty:
            dqs_observation_df = pd.DataFrame(columns=["service_pattern_stop_id"])

    return dqs_observation_df


def get_dqs_observations_df(
    service_pattern_df: pd.DataFrame, revision_ids=List
) -> pd.DataFrame:
    """Get Critical DQS Observations for the given service pattern stops

    Args:
        service_pattern_stops_df (pd.DataFrame): service pattern stop ids

    Returns:
        pd.DataFrame: Dataframe with service pattern stops details
    """
    dqs_observation_df = pd.DataFrame(columns=["service_pattern_stop_id"])
    if not service_pattern_df.empty:
        task_result_ids_df = pd.DataFrame.from_records(
            TaskResults.objects.filter(
                dataquality_report__revision_id__in=revision_ids,
                transmodel_txcfileattributes_id__in=list(
                    service_pattern_df["txcfileattributes_id"]
                ),
                checks__importance=Level.critical.value,
            ).values("id", "transmodel_txcfileattributes_id")
        )

        if not task_result_ids_df.empty:
            observation_result_qs = ObservationResults.objects.filter(
                taskresults_id__in=list(task_result_ids_df["id"]),
                service_pattern_stop_id__isnull=False,
            ).values("taskresults_id", "service_pattern_stop_id")

            dqs_observation_df = pd.DataFrame.from_records(observation_result_qs)

            if not dqs_observation_df.empty:
                dqs_observation_df = dqs_observation_df.merge(
                    task_result_ids_df,
                    how="left",
                    left_on="taskresults_id",
                    right_on="id",
                )

        if dqs_observation_df.empty:
            dqs_observation_df = pd.DataFrame(columns=["service_pattern_stop_id"])

    return dqs_observation_df[["service_pattern_stop_id"]]


def get_consumer_feedback_df(service_pattern_ids_df: pd.DataFrame) -> pd.DataFrame:
    """Get consumer feedback records for the given service pattern ids

    Args:
        service_pattern_ids_df (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: Dataframe with consumer feedback records
    """
    consumer_feedback_df = pd.DataFrame.from_records(
        ConsumerFeedback.objects.filter(
            service_id__in=list(service_pattern_ids_df["service_id"]),
        )
        .exclude(is_suppressed=True)
        .values("service_id")
    )
    if consumer_feedback_df.empty:
        consumer_feedback_df = pd.DataFrame(columns=["service_id"])
    return consumer_feedback_df


def get_licence_organisation_map(licence_list: list) -> dict:
    licence_organisation_name_map = dict()
    licence_qs = Licence.objects.filter(number__in=licence_list)
    for record in licence_qs:
        licence_organisation_name_map[record.number] = {
            "id": record.organisation.id,
            "name": record.organisation.name,
        }
    return licence_organisation_name_map
