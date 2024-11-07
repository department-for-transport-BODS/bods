from datetime import datetime, timedelta

from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.organisation.models import Organisation
from transit_odp.otc.constants import (
    OTC_SCOPE_STATUS_IN_SCOPE,
    OTC_SCOPE_STATUS_OUT_OF_SCOPE,
    UNDER_MAINTENANCE,
)


def get_overall_requires_attention(otc_service: dict) -> str:
    """
    Returns value for 'Requires attention' column based on the following logic:
        If 'Scope Status' = Out of Scope OR 'Seasonal Status' = Out of Season,
        then 'Requires attention' = No.
        If 'Timetables requires attention' = No AND 'AVL requires attention' = No,
        then 'Requires attention' = No.
        If 'Timetables requires attention' = Yes OR 'AVL requires attention' = Yes,
        then 'Requires attention' = Yes.

    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        str: Yes or No for 'Requires attention' column
    """
    timetable_requires_attention = otc_service.get("timetable_requires_attention")
    avl_requires_attention = otc_service.get("avl_requires_attention")
    scope_status = otc_service.get("scope_status")
    seasonal_status = otc_service.get("seasonal_status")

    if (scope_status == "Out of Scope") or (seasonal_status == "Out of Season"):
        return "No"
    if (timetable_requires_attention == "No") and (avl_requires_attention == "No"):
        return "No"
    return "Yes"


def get_avl_requires_attention(otc_service: dict) -> str:
    """
    Returns value for 'AVL requires attention' column based on the following logic:
        If both 'AVL Published Status' or 'AVL to Timetable Match Status' equal to Yes,
        then 'AVL requires attention' = No.
        If both 'AVL Published Status' or 'AVL to Timetable Match Status' equal to No,
        then 'AVL requires attention' = Yes.

    Args:
        avl_published_status (str): Value of 'AVL Published Status'
        avl_to_timetable__match_status (str): Value of 'AVL to Timetable Match Status'

    Returns:
        str: Yes or No for 'AVL requires attention' column
    """
    avl_published_status = otc_service.get("avl_published_status")
    avl_to_timetable_match_status = otc_service.get("avl_to_timetable_match_status")

    if (avl_published_status == "Yes") and (avl_to_timetable_match_status == "Yes"):
        return "No"
    return "Yes"


def get_avl_published_status(otc_service: dict) -> str:
    abods_registry = AbodsRegistery()
    synced_in_last_month = abods_registry.records()
    operator_ref = otc_service.get("national_operator_code")
    line_name = otc_service.get("otc_service_number")

    if f"{line_name}__{operator_ref}" in synced_in_last_month:
        return "Yes"
    return "No"


def get_avl_to_timetable_match_status(otc_service: dict) -> str:
    uncounted_activity_df = get_vehicle_activity_operatorref_linename()
    operator_ref = otc_service.get("national_operator_code")
    line_name = otc_service.get("otc_service_number")

    if not uncounted_activity_df.loc[
        (uncounted_activity_df["OperatorRef"] == operator_ref)
        & (
            uncounted_activity_df["LineRef"].isin(
                [line_name, line_name.replace(" ", "_")]
            )
        )
    ].empty:
        return "Yes"
    return "No"


def get_42_day_look_ahead_date() -> str:
    """
    Returns date for the 'Date for complete 42 day look ahead' column by
    calculating 42 days from now.

    Returns:
        str: Date (Today + 42 days)
    """
    # Calculate today's date and the date 42 days from now
    return (datetime.now() + timedelta(days=42)).strftime("%Y-%m-%d")


def get_seasonal_service_status(otc_service: dict) -> str:
    """
    Returns value for the 'Seasonal Status' column.

    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        str: Seasonal Status value
    """
    seasonal_service_status = otc_service.get("seasonal_status")
    return "In Season" if seasonal_service_status else "Out of Season"


def get_operator_name(otc_service: dict) -> str:
    """
    Returns value for the 'Operator Name' column by looking at the existence
    of a licence number in the 'Organisation' table.

    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        str: Operator name value
    """
    otc_licence_number = otc_service.get("otc_licence_number")
    operator_name = Organisation.objects.get_organisation_name(otc_licence_number)
    if not operator_name:
        return "Organisation not yet created"
    else:
        return operator_name


header_accessor_data_line_level = [
    (
        "Registration:Registration Number",
        lambda otc_service: otc_service.get("otc_registration_number"),
    ),
    (
        "Registration:Service Number",
        lambda otc_service: otc_service.get("otc_service_number"),
    ),
    (
        "Registration Status",
        lambda otc_service: (
            "Registered" if otc_service.get("otc_licence_number") else "Unregistered"
        ),
    ),
    (
        "Scope Status",
        lambda otc_service: (
            OTC_SCOPE_STATUS_OUT_OF_SCOPE
            if otc_service.get("scope_status", False)
            else OTC_SCOPE_STATUS_IN_SCOPE
        ),
    ),
    (
        "Seasonal Status",
        lambda otc_service: (
            get_seasonal_service_status(otc_service)
            if otc_service.get("seasonal_status") is not None
            else "Not Seasonal"
        ),
    ),
    (
        "Organisation Name",
        lambda otc_service: (
            get_operator_name(otc_service)
            if otc_service.get("operator_name") is None
            or otc_service.get("operator_name") == ""
            else otc_service.get("operator_name")
        ),
    ),
    (
        "Requires Attention",
        lambda otc_service: get_overall_requires_attention(otc_service),
    ),
    (
        "Timetables requires attention",
        lambda otc_service: otc_service.get("require_attention"),
    ),
    (
        "Timetables Published Status",
        lambda otc_service: (
            "Published" if otc_service.get("dataset_id") else "Unpublished"
        ),
    ),
    (
        "Timetables Timeliness Status",
        lambda otc_service: otc_service.get("staleness_status"),
    ),
    ("Timetables critical DQ issues", lambda otc_service: UNDER_MAINTENANCE),
    (
        "AVL requires attention",
        lambda otc_service: get_avl_requires_attention(otc_service),
    ),
    (
        "AVL Published Status",
        lambda otc_service: get_avl_published_status(otc_service),
    ),
    (
        "AVL to Timetable Match Status",
        lambda otc_service: get_avl_to_timetable_match_status(otc_service),
    ),
    ("Fares requires attention", lambda otc_service: UNDER_MAINTENANCE),
    ("Fares Published Status", lambda otc_service: UNDER_MAINTENANCE),
    ("Fares Timeliness Status", lambda otc_service: UNDER_MAINTENANCE),
    ("Fares Compliance Status", lambda otc_service: UNDER_MAINTENANCE),
    ("Timetables Data set ID", lambda otc_service: otc_service.get("dataset_id")),
    ("TXC:Filename", lambda otc_service: otc_service.get("xml_filename")),
    (
        "TXC:NOC",
        lambda otc_service: otc_service.get("national_operator_code"),
    ),
    (
        "TXC:Last Modified Date",
        lambda otc_service: otc_service.get("last_modified_date"),
    ),
    (
        "Date when timetable data is over 1 year old",
        lambda otc_service: otc_service.get("effective_stale_date_last_modified_date"),
    ),
    (
        "TXC:Operating Period End Date",
        lambda otc_service: otc_service.get("operating_period_end_date"),
    ),
    ("Fares Data set ID", lambda otc_service: UNDER_MAINTENANCE),
    ("NETEX:Filename", lambda otc_service: UNDER_MAINTENANCE),
    (
        "NETEX:Last Modified Date",
        lambda otc_service: UNDER_MAINTENANCE,
    ),
    (
        "Date when fares data is over 1 year old",
        lambda otc_service: UNDER_MAINTENANCE,
    ),
    (
        "NETEX:Operating Period End Date",
        lambda otc_service: UNDER_MAINTENANCE,
    ),
    (
        "Date Registration variation needs to be published",
        lambda otc_service: otc_service.get("effective_stale_date_otc_effective_date"),
    ),
    (
        "Date for complete 42 day look ahead",
        lambda otc_service: get_42_day_look_ahead_date(),
    ),
    (
        "Date seasonal service should be published",
        lambda otc_service: otc_service.get("effective_seasonal_start_date"),
    ),
    ("Seasonal Start Date", lambda otc_service: otc_service.get("seasonal_start")),
    ("Seasonal End Date", lambda otc_service: otc_service.get("seasonal_end")),
    (
        "Registration:Operator Name",
        lambda otc_service: otc_service.get("otc_operator"),
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
        "Registration:Expiry Date",
        lambda otc_service: otc_service.get("otc_licence_expiry_date"),
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
