from datetime import datetime, timedelta

from transit_odp.organisation.models import Organisation
from transit_odp.otc.constants import (
    OTC_SCOPE_STATUS_IN_SCOPE,
    OTC_SCOPE_STATUS_OUT_OF_SCOPE,
    UNDER_MAINTENANCE,
)


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


header_accessor_data = [
    ("XML:Service Code", lambda otc_service: otc_service.get("service_code")),
    ("XML:Line Name", lambda otc_service: otc_service.get("line_name")),
    (
        "Requires Attention",
        lambda otc_service: otc_service.get("require_attention"),
    ),
    (
        "Published Status",
        lambda otc_service: (
            "Published" if otc_service.get("dataset_id") else "Unpublished"
        ),
    ),
    (
        "OTC Status",
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
    ("Timeliness Status", lambda otc_service: otc_service.get("staleness_status")),
    (
        "Organisation Name",
        lambda otc_service: (
            get_operator_name(otc_service)
            if otc_service.get("operator_name") is None
            or otc_service.get("operator_name") == ""
            else otc_service.get("operator_name")
        ),
    ),
    ("Dataset ID", lambda otc_service: otc_service.get("dataset_id")),
    (
        "Date OTC variation needs to be published",
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
    ("XML:Filename", lambda otc_service: otc_service.get("xml_filename")),
    (
        "XML:Last Modified Date",
        lambda otc_service: otc_service.get("last_modified_date"),
    ),
    (
        "XML:National Operator Code",
        lambda otc_service: otc_service.get("national_operator_code"),
    ),
    ("XML:Licence Number", lambda otc_service: otc_service.get("licence_number")),
    ("XML:Revision Number", lambda otc_service: otc_service.get("revision_number")),
    (
        "XML:Operating Period Start Date",
        lambda otc_service: otc_service.get("operating_period_start_date"),
    ),
    (
        "XML:Operating Period End Date",
        lambda otc_service: otc_service.get("operating_period_end_date"),
    ),
    (
        "OTC:Licence Number",
        lambda otc_service: otc_service.get("otc_licence_number"),
    ),
    (
        "OTC:Registration Number",
        lambda otc_service: otc_service.get("otc_registration_number"),
    ),
    (
        "OTC:Service Number",
        lambda otc_service: otc_service.get("otc_service_number"),
    ),
    ("Traveline Region", lambda otc_service: otc_service.get("traveline_region")),
    (
        "Local Transport Authority",
        lambda otc_service: otc_service.get("ui_lta_name"),
    ),
]

header_accessor_data_compliance_report = [
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
        lambda otc_service: otc_service.get("overall_requires_attention"),
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
    (
        "Timetables critical DQ issues",
        lambda otc_service: otc_service.get("dq_require_attention"),
    ),
    (
        "AVL requires attention",
        lambda otc_service: otc_service.get("avl_requires_attention"),
    ),
    (
        "AVL Published Status",
        lambda otc_service: otc_service.get("avl_published_status"),
    ),
    (
        "Error in AVL to Timetable Matching",
        lambda otc_service: otc_service.get("error_in_avl_to_timetable_matching"),
    ),
    (
        "Fares requires attention",
        lambda otc_service: otc_service.get("fares_requires_attention"),
    ),
    (
        "Fares Published Status",
        lambda otc_service: otc_service.get("fares_published_status"),
    ),
    (
        "Fares Timeliness Status",
        lambda otc_service: otc_service.get("fares_timeliness_status"),
    ),
    (
        "Fares Compliance Status",
        lambda otc_service: otc_service.get("fares_compliance_status"),
    ),
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
    ("Fares Data set ID", lambda otc_service: otc_service.get("fares_dataset_id")),
    ("NETEX:Filename", lambda otc_service: otc_service.get("fares_filename")),
    (
        "NETEX:Last Modified Date",
        lambda otc_service: otc_service.get("fares_last_modified"),
    ),
    (
        "Date when fares data is over 1 year old",
        lambda otc_service: otc_service.get("fares_one_year_date"),
    ),
    (
        "NETEX:Operating Period End Date",
        lambda otc_service: otc_service.get("fares_operating_period_end"),
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
        "Requires Attention",
        lambda otc_service: otc_service.get("require_attention"),
    ),
    (
        "Published Status",
        lambda otc_service: (
            "Published" if otc_service.get("dataset_id") else "Unpublished"
        ),
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
    ("Timeliness Status", lambda otc_service: otc_service.get("staleness_status")),
    (
        "Organisation Name",
        lambda otc_service: (
            get_operator_name(otc_service)
            if otc_service.get("operator_name") is None
            or otc_service.get("operator_name") == ""
            else otc_service.get("operator_name")
        ),
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

header_accessor_data_db_compliance_report = [
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
        lambda otc_service: otc_service.get("scope_status"),
    ),
    (
        "Seasonal Status",
        lambda otc_service: otc_service.get("seasonal_status"),
    ),
    (
        "Organisation Name",
        lambda otc_service: otc_service.get("operator_name"),
    ),
    (
        "Requires Attention",
        lambda otc_service: otc_service.get("overall_requires_attention"),
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
    (
        "Timetables critical DQ issues",
        lambda otc_service: otc_service.get("dq_require_attention"),
    ),
    (
        "AVL requires attention",
        lambda otc_service: otc_service.get("avl_requires_attention"),
    ),
    (
        "AVL Published Status",
        lambda otc_service: otc_service.get("avl_published_status"),
    ),
    (
        "Error in AVL to Timetable Matching",
        lambda otc_service: otc_service.get("error_in_avl_to_timetable_matching"),
    ),
    (
        "Fares requires attention",
        lambda otc_service: otc_service.get("fares_requires_attention"),
    ),
    (
        "Fares Published Status",
        lambda otc_service: otc_service.get("fares_published_status"),
    ),
    (
        "Fares Timeliness Status",
        lambda otc_service: otc_service.get("fares_timeliness_status"),
    ),
    (
        "Fares Compliance Status",
        lambda otc_service: otc_service.get("fares_compliance_status"),
    ),
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
        "TXC:Operating Period Start Date",
        lambda otc_service: otc_service.get("operating_period_start_date"),
    ),
    (
        "TXC:Operating Period End Date",
        lambda otc_service: otc_service.get("operating_period_end_date"),
    ),
    (
        "Fares Data set ID",
        lambda otc_service: (
            UNDER_MAINTENANCE
            if otc_service.get("fares_filename") == UNDER_MAINTENANCE
            else otc_service.get("fares_dataset_id")
        ),
    ),
    ("NETEX:Filename", lambda otc_service: otc_service.get("fares_filename")),
    (
        "NETEX:Last Modified Date",
        lambda otc_service: (
            otc_service.get("fares_last_modified")
            if otc_service.get("fares_filename") != UNDER_MAINTENANCE
            else UNDER_MAINTENANCE
        ),
    ),
    (
        "Date when fares data is over 1 year old",
        lambda otc_service: (
            otc_service.get("fares_one_year_date")
            if otc_service.get("fares_filename") != UNDER_MAINTENANCE
            else UNDER_MAINTENANCE
        ),
    ),
    (
        "NETEX:Operating Period End Date",
        lambda otc_service: (
            otc_service.get("fares_operating_period_end")
            if otc_service.get("fares_filename") != UNDER_MAINTENANCE
            else UNDER_MAINTENANCE
        ),
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
    (
        "TXC: Revision Number",
        lambda otc_service: otc_service.get("revision_number"),
    ),
    (
        "TXC: Derived Termination Date",
        lambda otc_service: otc_service.get("derived_termination_date"),
    ),
]
