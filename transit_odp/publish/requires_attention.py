import logging
import pandas as pd
from datetime import timedelta
from typing import Dict, List, Optional

from django.db.models import Subquery
from django.utils.timezone import now
from waffle import flag_is_active

from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.common.constants import FeatureFlags
from transit_odp.dqs.constants import Level
from transit_odp.dqs.models import ObservationResults
from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.organisation.models.organisations import ConsumerFeedback
from transit_odp.otc.models import Service as OTCService
from transit_odp.transmodel.models import (
    Service as TransmodelService,
    ServicePatternStop,
)
from django.db.models import Q


logger = logging.getLogger(__name__)


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
            .order_by(
                "service_code",
                "-revision__published_at",
                "-revision_number",
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
    if not line_number:
        object_list.append(
            {
                "licence_number": service.otc_licence_number,
                "service_code": service.registration_number,
                "line_number": service.service_number,
            }
        )
    else:
        object_list.append(
            {
                "licence_number": service.otc_licence_number,
                "service_code": service.registration_number,
                "line_number": line_number,
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
        Staleness Status - Stale - 12 months old:
            If Staleness status is not OTC Variation
            AND
            Staleness status is not 42 day look ahead
            AND
            last_modified + 365 days <= today
    """
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
    staleness_42_day_look_ahead = (
        (not staleness_otc and operating_period_end_date < forty_two_days_from_today)
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
    return any(evaluate_staleness(service, file_attribute))


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
            _update_data(object_list, service)
        elif is_stale(service, file_attribute) or (
            is_dqs_require_attention
            and service_key in dqs_critical_issues_service_line_map
        ):
            _update_data(object_list, service)
    return object_list


def get_avl_requires_attention_line_level_data(org_id: int) -> List[Dict[str, str]]:
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

    uncounted_activity_df = get_vehicle_activity_operatorref_linename()
    abods_registry = AbodsRegistery()
    synced_in_last_month = abods_registry.records()

    for service_key, service in otc_map.items():
        file_attribute = txcfa_map.get(service_key)
        if file_attribute is not None:
            operator_ref = file_attribute.national_operator_code
            line_name = service_key[1]

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
                _update_data(object_list, service)
        elif (
            is_dqs_require_attention
            and (service_key, service) in dqs_critical_issues_service_line_map
        ):
            _update_data(object_list, service)
        else:
            _update_data(object_list, service)
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
    timetables_lta_services_requiring_attention = 0
    otc_map = get_line_level_otc_map_lta(lta_list)
    txcfa_map = get_line_level_txc_map_lta(lta_list)
    for (service_number, registration_number), service in otc_map.items():
        file_attribute = txcfa_map.get((service_number, registration_number))
        if file_attribute is None:
            _update_data(object_list, service, line_number=service_number)
        elif is_stale(service, file_attribute):
            _update_data(object_list, service, line_number=service_number)
    timetables_lta_services_requiring_attention = len(object_list)
    print(
        f"timetables_lta_services_requiring_attention: {timetables_lta_services_requiring_attention}"
    )
    return timetables_lta_services_requiring_attention


def get_avl_records_require_attention_lta_line_level_length(lta_list: List) -> int:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. service has
    been published for a service or has a matching issue.

    Returns list of objects of each service requiring attention for an organisation.
    """
    object_list = []
    otc_map = get_line_level_otc_map_lta(lta_list)
    txcfa_map = get_line_level_txc_map_lta(lta_list)
    service_codes = [service_code for (service_code, line_name) in otc_map]
    txcfa_map = get_line_level_txc_map_service_base(service_codes)
    uncounted_activity_df = get_vehicle_activity_operatorref_linename()
    abods_registry = AbodsRegistery()
    synced_in_last_month = abods_registry.records()

    for service_key, service in otc_map.items():
        file_attribute = txcfa_map.get(service_key)
        if file_attribute is not None:
            operator_ref = file_attribute.national_operator_code
            line_name = service_key[1]

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
                _update_data(object_list, service)
        else:
            _update_data(object_list, service)
    return len(object_list)


def get_fares_records_require_attention_lta_line_level_length(lta_list: List) -> int:
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
        int: The count of services requiring attention.
    """
    object_list = []
    otc_map = get_line_level_otc_map_lta(lta_list)
    txcfa_map = get_line_level_txc_map_lta(lta_list)
    service_codes = [service_code for (service_code, line_name) in otc_map]
    txcfa_map = get_line_level_txc_map_service_base(service_codes)
    fares_df = get_fares_dataset_map(txcfa_map)

    for service_key, service in otc_map.items():

        file_attribute = txcfa_map.get(service_key)
        # If no file attribute (TxcFileAttribute), service requires attention
        if file_attribute is None:
            _update_data(object_list, service)
        elif fares_df.empty:
            _update_data(object_list, service)
        else:
            noc = file_attribute.national_operator_code
            line_name = file_attribute.line_name_unnested
            df = fares_df[
                (fares_df.national_operator_code == noc)
                & (fares_df.line_name == line_name)
            ]
            if not df.empty:
                row = df.iloc[0].to_dict()
                valid_to = row.get("valid_to", None)
                last_modified_date = row.get("last_updated_date", "")
                valid_to = date.today() if pd.isnull(valid_to) else valid_to
                last_modified_date = (
                    datetime.now()
                    if pd.isnull(last_modified_date)
                    else last_modified_date
                )
                if is_fares_stale(valid_to, last_modified_date):
                    _update_data(object_list, service)
    return len(object_list)


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
    object_list = []
    dqs_critical_issues_service_line_map = []
    lta_services_requiring_attention = 0
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
    lta_services_requiring_attention = len(object_list)

    return lta_services_requiring_attention


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


def query_dq_critical_observation(query) -> List[tuple]:
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

    1. Get dataframe to get service_patter_ids for the given query of registration number, line name, revision id
    2. Get dataframe by querying servicepatternstops table from the service_pattern_ids extracted in step 1
    3. Merge the dataframe built on step 1 and step 2 with left join (To prevent any service.id loss)
    4. Get the observations with ciritical type and merge the selected stop points with the Step 3 dataframe
    5. Now to get consumer feedback use the service_ids extracted on Step 1 df and search for feedbacks which are not suppressed
    6. Merge the dataframe of consumer feedbacks with main dataframe
    7. Return the registration number and line name for which any value (Observation with ciritical or Consumer feedback) is present

    Returns:
        dict[tuple, str]: return a list of services"""

    service_pattern_ids_df = get_service_patterns_df(query)
    if service_pattern_ids_df.empty:
        return []

    service_pattern_stops_df = get_service_pattern_stops_df(service_pattern_ids_df)

    service_pattern_ids_df = service_pattern_ids_df.merge(
        service_pattern_stops_df, on=["service_pattern_id"], how="left"
    )

    dqs_observation_df = get_dqs_observations_df(service_pattern_stops_df)

    dqs_require_attention_df = service_pattern_ids_df.merge(
        dqs_observation_df, on=["service_pattern_stop_id"], how="left", indicator=True
    )
    dqs_require_attention_df.rename(columns={"_merge": "dqs_critical"}, inplace=True)

    is_specific_feedback = flag_is_active("", "is_specific_feedback")
    if is_specific_feedback:
        consumer_feedback_df = get_consumer_feedback_df(service_pattern_ids_df)

        dqs_require_attention_df = dqs_require_attention_df.merge(
            consumer_feedback_df, on=["service_id"], how="left", indicator=True
        )
        dqs_require_attention_df.rename(
            columns={"_merge": "has_feedback"}, inplace=True
        )

        dqs_require_attention_df = dqs_require_attention_df[
            (dqs_require_attention_df["dqs_critical"] == "both")
            | (dqs_require_attention_df["has_feedback"] == "both")
        ]
    else:
        dqs_require_attention_df = dqs_require_attention_df[
            dqs_require_attention_df["dqs_critical"] == "both"
        ]

    dqs_require_attention_df = dqs_require_attention_df[["service_code", "line_name"]]

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
    for _, row in txc_map.iterrows():
        query |= Q(
            service_code=row["service_code"],
            service_patterns__line_name=row["line_name_unnested"],
            revision_id=row["revision_id"],
            txcfileattributes_id=row["id"],
        )
    return query_dq_critical_observation(query)


def get_service_patterns_df(query) -> pd.DataFrame:
    """Get list fo service pattern records for service pattern ids

    Args:
        query (_type_): Servie pattner filter (OR query)

    Returns:
        pd.DataFrame: Dataframe with list of transmodel service with service pattern id
    """
    service_pattern_ids_df = pd.DataFrame.from_records(
        TransmodelService.objects.filter(query).values(
            "id", "service_code", "service_patterns__line_name", "service_patterns__id"
        )
    )
    if service_pattern_ids_df.empty:
        service_pattern_ids_df = pd.DataFrame(
            columns=[
                "id",
                "service_code",
                "service_patterns__line_name",
                "service_patterns__id",
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


def get_service_pattern_stops_df(service_pattern_ids_df: pd.DataFrame) -> pd.DataFrame:
    """Get Service pattern stop ids for given service pattern ids

    Args:
        service_pattern_ids_df (pd.DataFrame): Dataframe with service pattern ids

    Returns:
        pd.DataFrame: Dataframe with service pattern stop ids
    """
    service_pattern_stops_df = pd.DataFrame.from_records(
        ServicePatternStop.objects.filter(
            service_pattern_id__in=list(service_pattern_ids_df["service_pattern_id"])
        ).values("id", "service_pattern_id")
    )
    if service_pattern_stops_df.empty:
        service_pattern_stops_df = pd.DataFrame(columns=["id", "service_pattern_id"])

    service_pattern_stops_df.rename(
        columns={"id": "service_pattern_stop_id"}, inplace=True
    )
    return service_pattern_stops_df


def get_dqs_observations_df(service_pattern_stops_df: pd.DataFrame) -> pd.DataFrame:
    """Get Critical DQS Observations for the given service pattern stops

    Args:
        service_pattern_stops_df (pd.DataFrame): service pattern stop ids

    Returns:
        pd.DataFrame: Dataframe with service pattern stops details
    """
    dqs_observation_df = pd.DataFrame(columns=["service_pattern_stop_id"])
    if not service_pattern_stops_df.empty:
        dqs_observation_df = pd.DataFrame.from_records(
            ObservationResults.objects.filter(
                service_pattern_stop_id__in=list(
                    service_pattern_stops_df["service_pattern_stop_id"]
                ),
                taskresults__checks__importance=Level.critical.value,
            ).values("service_pattern_stop_id")
        )

        if dqs_observation_df.empty:
            dqs_observation_df = pd.DataFrame(columns=["service_pattern_stop_id"])

    return dqs_observation_df


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
