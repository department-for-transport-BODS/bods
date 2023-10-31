from datetime import datetime, timedelta
from transit_odp.organisation.models import Organisation


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


header_accessor_data = [
    ("XML:Service Code", lambda otc_service: otc_service.get("service_code")),
    ("XML:Line Name", lambda otc_service: otc_service.get("line_number")),
    ("Requires Attention", lambda otc_service: otc_service.get("require_attention")),
    (
        "Published Status",
        lambda otc_service: "Published"
        if otc_service.get("dataset_id")
        else "Unpublished",
    ),
    (
        "OTC Status",
        lambda otc_service: "Registered"
        if otc_service.get("otc_licence_number")
        else "Unregistered",
    ),
    (
        "Scope Status",
        lambda otc_service: "Out of Scope"
        if otc_service.get("scope_status")
        else "In Scope",
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
    ("OTC:Licence Number", lambda otc_service: otc_service.get("otc_licence_number")),
    (
        "OTC:Registration Number",
        lambda otc_service: otc_service.get("otc_registration_number"),
    ),
    ("OTC:Service Number", lambda otc_service: otc_service.get("otc_service_number")),
]
