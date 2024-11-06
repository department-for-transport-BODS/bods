from transit_odp.browse.common import (
    get_42_day_look_ahead_date,
    get_avl_requires_attention,
    get_operator_name,
    get_overall_requires_attention,
    get_scope_status,
    get_seasonal_service_status,
)
from transit_odp.otc.constants import UNDER_MAINTENANCE

header_accessor_data = [
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
        lambda otc_service: get_scope_status(otc_service),
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
        lambda otc_service: otc_service.get("timetable_requires_attention"),
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
        lambda otc_service: otc_service.get("avl_published_status"),
    ),
    (
        "AVL to Timetable Match Status",
        lambda otc_service: otc_service.get("avl_to_timetable_match_status"),
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
