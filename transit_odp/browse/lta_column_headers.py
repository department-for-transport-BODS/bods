from datetime import datetime, timedelta

from transit_odp.organisation.models import Organisation
from transit_odp.otc.constants import (
    OTC_SCOPE_STATUS_IN_SCOPE,
    OTC_SCOPE_STATUS_OUT_OF_SCOPE,
)
from transit_odp.otc.models import Licence as OTCLicence
from transit_odp.otc.models import Operator as OTCOperator


def get_42_day_look_ahead_date() -> str:
    # Calculate today's date and the date 42 days from now
    return (datetime.now() + timedelta(days=42)).strftime("%Y-%m-%d")


def get_seasonal_service_status(otc_service: dict) -> str:
    seasonal_service_status = otc_service.get("seasonal_status")
    return "In Season" if seasonal_service_status else "Out of Season"


def get_operator_name(otc_service: dict) -> str:
    otc_licence_number = otc_service.get("otc_licence_number")
    operator_name = Organisation.objects.get_organisation_name(otc_licence_number)
    if not operator_name:
        return "Organisation not yet created"
    else:
        return operator_name


def get_otc_operator_name(otc_service: dict) -> str:
    """
    Retrieves the operator name from OTC Operator table.


    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        str: Returns the operator name from the OTC
    """
    otc_operator = otc_service.get("otc_operator")
    otc_operator_id = getattr(otc_operator, "id", None)
    otc_operator_name = OTCOperator.objects.filter(id=otc_operator_id).values_list(
        "operator_name", flat=True
    )[0]
    return otc_operator_name


def get_otc_licence_id(otc_service: dict) -> int:
    """
    Function to retrieve the id from the licence object
    in the OTC Service table.

    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        int: Returns the licence id
    """
    otc_licence = otc_service.get("otc_licence")
    return getattr(otc_licence, "id", None)


def get_granted_date(otc_service: dict) -> str:
    """
    Retrieves granted date from OTC Licence table.

    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        str: Returns the granted date for licence

    """
    otc_licence_id = get_otc_licence_id(otc_service)
    granted_date = OTCLicence.objects.filter(id=otc_licence_id).values_list(
        "granted_date", flat=True
    )[0]
    return granted_date


def get_expiry_date(otc_service: dict) -> str:
    """
    Retrieves expiry date from OTC Licence table.

    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        str: Returns the expiry date for licence
    """
    otc_licence_id = get_otc_licence_id(otc_service)
    expiry_date = OTCLicence.objects.filter(id=otc_licence_id).values_list(
        "expiry_date", flat=True
    )[0]
    return expiry_date


header_accessor_data = [
    (
        "Registration:Registration Number",
        lambda otc_service: otc_service.get("otc_registration_number"),
    ),
    (
        "Registration:Service Number",
        lambda otc_service: otc_service.get("otc_service_number"),
    ),
    ("Requires Attention", lambda otc_service: otc_service.get("require_attention")),
    (
        "Published Status",
        lambda otc_service: "Published"
        if otc_service.get("dataset_id")
        else "Unpublished",
    ),
    (
        "Registration Status",
        lambda otc_service: "Registered"
        if otc_service.get("otc_licence_number")
        else "Unregistered",
    ),
    (
        "Scope Status",
        lambda otc_service: OTC_SCOPE_STATUS_OUT_OF_SCOPE
        if otc_service.get("scope_status", False)
        else OTC_SCOPE_STATUS_IN_SCOPE,
    ),
    (
        "Seasonal Status",
        lambda otc_service: get_seasonal_service_status(otc_service)
        if otc_service.get("seasonal_status") is not None
        else "Not Seasonal",
    ),
    ("Timeliness Status", lambda otc_service: otc_service.get("staleness_status")),
    (
        "Organisation Name",
        lambda otc_service: get_operator_name(otc_service)
        if otc_service.get("operator_name") is None
        or otc_service.get("operator_name") == ""
        else otc_service.get("operator_name"),
    ),
    ("Data set ID", lambda otc_service: otc_service.get("dataset_id")),
    ("XML:Filename", lambda otc_service: otc_service.get("xml_filename")),
    (
        "XML:Last Modified Date",
        lambda otc_service: otc_service.get("last_modified_date"),
    ),
    (
        "XML:Operating Period End Date",
        lambda otc_service: otc_service.get("operating_period_end_date"),
    ),
    (
        "Date Registration variation needs to be published",
        lambda otc_service: otc_service.get("effective_stale_date_otc_effective_date"),
    ),
    (
        "Date for complete 42-day look ahead",
        lambda otc_service: get_42_day_look_ahead_date(),
    ),
    (
        "Date when data is over 1 year old",
        lambda otc_service: otc_service.get("effective_stale_date_last_modified_date"),
    ),
    (
        "Date seasonal service should be published",
        lambda otc_service: otc_service.get("effective_seasonal_start_date"),
    ),
    ("Seasonal Start Date", lambda otc_service: otc_service.get("seasonal_start")),
    ("Seasonal End Date", lambda otc_service: otc_service.get("seasonal_end")),
    (
        "Registration:Operator Name",
        lambda otc_service: get_otc_operator_name(otc_service),
    ),
    (
        "Registration:Licence Number",
        lambda otc_service: otc_service.get("otc_licence_number"),
    ),
    (
        "Registration:Service Type Description",
        lambda otc_service: otc_service.get("otc_service_type_description"),
    ),
    (
        "Registration:Variation Number",
        lambda otc_service: otc_service.get("otc_variation_number"),
    ),
    (
        "Registration:Start Point",
        lambda otc_service: otc_service.get("otc_start_point"),
    ),
    (
        "Registration:Finish Point",
        lambda otc_service: otc_service.get("otc_finish_point"),
    ),
    ("Registration:Via", lambda otc_service: otc_service.get("otc_via")),
    (
        "Registration:Granted Date",
        lambda otc_service: get_granted_date(otc_service),
    ),
    (
        "Registration:Expiry Date",
        lambda otc_service: get_expiry_date(otc_service),
    ),
    (
        "Registration:Effective Date",
        lambda otc_service: otc_service.get("otc_effective_date"),
    ),
    (
        "Registration:Received Date",
        lambda otc_service: otc_service.get("otc_received_date"),
    ),
    ("Traveline Region", lambda otc_service: otc_service.get("traveline_region")),
    (
        "Local Transport Authority",
        lambda otc_service: otc_service.get("ui_lta_name"),
    ),
]
