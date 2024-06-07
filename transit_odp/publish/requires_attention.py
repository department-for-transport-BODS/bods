from typing import Dict, List
import copy

from django.db.models import Subquery
from django.utils.timezone import now

from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.otc.models import Service as OTCService
from transit_odp.naptan.models import AdminArea
from datetime import timedelta


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


def get_line_level_txc_map_lta(lta_list) -> Dict[str, TXCFileAttributes]:
    """
    Get a list of dictionaries of live TXCFileAttributes for a LTA
    with relevant effective staleness dates annotated.
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


def _update_data(object_list: List[Dict[str, str]], service: OTCService) -> None:
    """
    Append data to object_list of services requiring attention.
    """
    object_list.append(
        {
            "licence_number": service.otc_licence_number,
            "service_code": service.registration_number,
            "line_number": service.service_number,
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

    otc_map = get_line_level_in_scope_otc_map(org_id)
    txcfa_map = get_line_level_txc_map(org_id)

    for service_key, service in otc_map.items():
        file_attribute = txcfa_map.get(service_key)
        if file_attribute is None:
            _update_data(object_list, service)
        elif is_stale(service, file_attribute):
            _update_data(object_list, service)
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
