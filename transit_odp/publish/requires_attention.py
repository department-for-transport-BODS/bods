from typing import Dict, List

from django.utils.timezone import now

from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.otc.models import Service as OTCService


def get_otc_map(org_id: int) -> Dict[str, OTCService]:
    """
    Get a list of dictionaries which includes all OTC Services for an organisation,
    excluding exempted services and Out of Season seasonal services.
    """
    return {
        service.registration_number.replace("/", ":"): service
        for service in OTCService.objects.get_otc_data_for_organisation(org_id)
    }


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
    }


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
        Staleness Status - Not Stale:
            Default status for service codes published to BODS
        Staleness Status - Stale - OTC Variation:
            If last_modified < OTC Service effective_date
            AND
            Today >= effective_stale_date_otc_effective_date
        Staleness Status - Stale - End Date Passed:
            If effective_stale_date_end_date (if present) <
                effective_stale_date_last_modified_date
            AND
            Today >= effective_stale_date_end_date
            AND
            last_modified >= OTC Service effective_date
        Staleness Status - Stale - 12 months old:
            If effective_stale_date_last_modified_date <
                effective_stale_date_end_date (if present)
            AND
            Today >= effective_stale_date_last_modified_date
            AND
            last_modified >= OTC Service effective_date
    """
    today = now().date()
    last_modified = file_attribute.modification_datetime.date()
    effective_stale_date_last_modified_date = (
        file_attribute.effective_stale_date_last_modified_date
    )
    effective_stale_date_end_date = file_attribute.effective_stale_date_end_date
    effective_date = service.effective_date
    effective_stale_date_otc_effective_date = (
        service.effective_stale_date_otc_effective_date
    )

    staleness_otc = (
        effective_date > last_modified
        and effective_stale_date_otc_effective_date <= today
    )
    staleness_end_date = (
        (
            effective_stale_date_end_date < effective_stale_date_last_modified_date
            and effective_stale_date_end_date <= today
            and effective_date <= last_modified
        )
        if effective_stale_date_end_date
        else False
    )
    staleness_12_months_old = (
        (
            effective_stale_date_last_modified_date < effective_stale_date_end_date
            and effective_stale_date_last_modified_date <= today
            and effective_date <= last_modified
        )
        if effective_stale_date_end_date
        else (
            effective_stale_date_last_modified_date <= today
            and effective_date <= last_modified
        )
    )

    return (
        staleness_end_date,
        staleness_12_months_old,
        staleness_otc,
    )


def is_stale(service: OTCService, file_attribute: TXCFileAttributes) -> bool:
    return any(evaluate_staleness(service, file_attribute))


def get_requires_attention_data(org_id: int) -> List[Dict[str, str]]:
    """
    Compares an organisation's OTC Services dictionaries list with TXCFileAttributes
    dictionaries list to determine which OTC Services require attention ie. not live
    in BODS at all, or live but meeting new Staleness conditions.

    Returns list of objects of each service requiring attention for an organisation.
    """
    object_list = []

    otc_map = get_otc_map(org_id)
    txcfa_map = get_txc_map(org_id)

    for service_code, service in otc_map.items():
        file_attribute = txcfa_map.get(service_code)
        if file_attribute is None:
            _update_data(object_list, service)
        elif is_stale(service, file_attribute):
            _update_data(object_list, service)
    return object_list
