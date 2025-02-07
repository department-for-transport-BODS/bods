import datetime
from collections import OrderedDict
from typing import List, Optional

import numpy as np
import pandas as pd
from pandas import Series
from waffle import flag_is_active

from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.common.collections import Column
from transit_odp.organisation.constants import (
    ENGLISH_TRAVELINE_REGIONS,
    TravelineRegions,
)
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.models import (
    Organisation,
    SeasonalService,
    ServiceCodeExemption,
    TXCFileAttributes,
)
from transit_odp.otc.constants import (
    OTC_SCOPE_STATUS_IN_SCOPE,
    OTC_SCOPE_STATUS_OUT_OF_SCOPE,
    OTC_STATUS_REGISTERED,
    OTC_STATUS_UNREGISTERED,
    UNDER_MAINTENANCE,
)
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import (
    get_dq_critical_observation_services_map_from_dataframe,
    get_fares_dataset_map,
    is_fares_stale,
)

TXC_COLUMNS = (
    "organisation_name",
    "dataset_id",
    "filename",
    "licence_number",
    "modification_datetime",
    "national_operator_code",
    "service_code",
    "public_use",
    "operating_period_start_date",
    "operating_period_end_date",
    "revision_number",
    "string_lines",
    "origin",
    "destination",
)

TXC_LINE_LEVEL_COLUMNS = TXC_COLUMNS + ("line_name_unnested", "revision_id")

OTC_COLUMNS = (
    "service_code",
    "otc_operator_id",
    "operator_name",
    "address",
    "otc_licence_number",
    "licence_status",
    "registration_number",
    "service_type_description",
    "variation_number",
    "service_number",
    "start_point",
    "finish_point",
    "via",
    "granted_date",
    "expiry_date",
    "effective_date",
    "received_date",
    "service_type_other_details",
    "traveline_region",
    "local_authority_ui_lta",
    "api_type",
)

SEASONAL_SERVICE_COLUMNS = ("registration_number", "start", "end")

TIMETABLE_COLUMN_MAP = OrderedDict(
    {
        "service_code": Column(
            "XML:Service Code",
            "The ServiceCode(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "string_lines": Column(
            "XML:Line Name",
            "The line name(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "requires_attention": Column(
            "Requires Attention",
            "No: </br>"
            "Default state for correctly published services, will be “No” "
            "unless any of the logic below is met. </br></br>"
            "Yes: </br>"
            "Yes If OTC status = Registered and Scope Status = In scope and "
            "Seasonal Status ≠ Out of season and Published Status = Unpublished. </br>"
            "Yes if OTC status = Registered and Scope Status = In scope and "
            "Seasonal Status ≠ Out of season and Published Status = Published "
            "and Timeliness Status ≠ Up to date. ",
        ),
        "published_status": Column(
            "Published Status",
            "Published: Published to BODS by an Operator/Agent. </br></br>"
            "Unpublished: Not published to BODS by an Operator/Agent.",
        ),
        "otc_status": Column(
            "OTC Status",
            "Registered: Registered and not cancelled within the OTC "
            "database. </br></br>"
            "Unregistered: Not Registered within the OTC.",
        ),
        "scope_status": Column(
            "Scope Status",
            "In scope: Default status for services registered with the OTC and "
            "other enhanced partnerships. </br></br>"
            "Out of Scope: Service code has been marked as exempt by the DVSA "
            "or the BODS team.",
        ),
        "seasonal_status": Column(
            "Seasonal Status",
            "In season: Service code has been marked as seasonal by the "
            "operator or their agent and todays date falls within the "
            "relevant date range for that service code.  </br></br>"
            "Out of Season: Service code has been marked as seasonal by "
            "the operator or their agent and todays date falls outside "
            "the relevant date range for that service code.  </br></br>"
            "Not Seasonal: Default status for published or unpublished services"
            "to BODS. </br> Assumed Not seasonal unless service code has been marked "
            "with a date range within the seasonal services flow.",
        ),
        "staleness_status": Column(
            "Timeliness Status",
            "Up to date: Default status for service codes published to BODS. </br></br>"
            "Timeliness checks are evaluated in this order: </br></br>"
            "1) OTC Variation not published: </br>"
            "If 'XML:Last modified date' is earlier than 'Date OTC variation needs "
            "to be published' </br> and </br> 'Date OTC variation needs to be "
            "published'is earlier than today's date.</br> and </br>"
            "No associated data has been published. </br>"
            "NB there are two association methods: </br> Method 1: </br>"
            "Data for that service code has been updated within 70 days before "
            "the OTC variation effective date.</br> Method 2: </br>"
            "Data for that service code has been updated with a 'XML:Operating "
            "Period Start Date' which equals OTC variation effective date. </br></br>"
            "2) 42 day look ahead is incomplete: </br> If not out of date due to  "
            "'OTC variation not published' </br> and </br> 'XML:Operating Period "
            "End Date' is earlier than 'Date for complete 42 day look "
            "ahead'. </br></br>"
            "3) Service hasn't been updated within a year: </br> If not out of date "
            "due to '42 day lookahead is incomplete' or 'OTC variation not published'"
            "</br> and </br> 'Date at which data is 1 year old' is earlier than "
            "today's date.",
        ),
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS.",
        ),
        "dataset_id": Column(
            "Data set ID",
            "The internal BODS generated ID of the dataset "
            "that contains the data for this row.",
        ),
        "effective_stale_date_from_otc_effective": Column(
            "Date OTC variation needs to be published",
            "OTC:Effective date from timetable data catalogue minus 42 days.",
        ),
        "date_42_day_look_ahead": Column(
            "Date for complete 42 day look ahead",
            "Today's date + 42 days.",
        ),
        "effective_stale_date_from_last_modified": Column(
            "Date when data is over 1 year old",
            "'XML:Last Modified date' from timetable data catalogue plus 12 months.",
        ),
        "effective_seasonal_start": Column(
            "Date seasonal service should be published",
            "If Seasonal Start Date is present, then Seasonal Start Date minus "
            "42 days, else null.",
        ),
        "seasonal_start": Column(
            "Seasonal Start Date",
            "If service has been assigned a date range from within the seasonal "
            "services flow, then take start date, else null.",
        ),
        "seasonal_end": Column(
            "Seasonal End Date",
            "If service has been assigned a date range from within the "
            "seasonal services flow, then take end date, else null.",
        ),
        "filename": Column(
            "XML:Filename",
            "The exact name of the file provided to BODS. This is usually "
            "generated by the publisher or their supplier.",
        ),
        "last_modified_date": Column(
            "XML:Last Modified Date",
            "Date of last modified file within the service codes dataset.",
        ),
        "national_operator_code": Column(
            "XML:National Operator Code",
            "The National Operator Code(s) as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "licence_number": Column(
            "XML:Licence Number",
            "The License number(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "public_use": Column(
            "XML:Public Use Flag",
            "The Public Use Flag element as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "revision_number": Column(
            "XML:Revision Number",
            "The service revision number date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "operating_period_start_date": Column(
            "XML:Operating Period Start Date",
            "The operating period start date as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "operating_period_end_date": Column(
            "XML:Operating Period End Date",
            "The operating period end date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "origin": Column(
            "OTC:Origin",
            "The origin element as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "destination": Column(
            "OTC:Destination",
            "The destination element as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "otc_operator_id": Column(
            "OTC:Operator ID",
            "The operator ID element as extracted from the OTC database.",
        ),
        "operator_name": Column(
            "OTC:Operator Name",
            "The operator name element as extracted from the OTC database.",
        ),
        "address": Column(
            "OTC:Address",
            "The address as extracted from the OTC database.",
        ),
        "otc_licence_number": Column(
            "OTC:Licence Number",
            "The licence number element as extracted from the OTC database.",
        ),
        "licence_status": Column(
            "OTC:Licence Status",
            "The licence status element as extracted from the OTC database.",
        ),
        "registration_number": Column(
            "OTC:Registration Number",
            "The registration number element as extracted from the OTC database.",
        ),
        "service_type_description": Column(
            "OTC:Service Type Description",
            "The service type description element as extracted from the OTC database.",
        ),
        "variation_number": Column(
            "OTC:Variation Number",
            "The variation number element as extracted from the OTC database.",
        ),
        "service_number": Column(
            "OTC:Service Number",
            "The service number element as extracted from the OTC database.",
        ),
        "start_point": Column(
            "OTC:Start Point",
            "The start point element as extracted from the OTC database.",
        ),
        "finish_point": Column(
            "OTC:Finish Point",
            "The finish point element as extracted from the OTC database.",
        ),
        "via": Column(
            "OTC:Via",
            "The via element as extracted from the OTC database.",
        ),
        "granted_date": Column(
            "OTC:Granted Date",
            "The granted date element as extracted from the OTC database.",
        ),
        "expiry_date": Column(
            "OTC:Expiry Date",
            "The expiry date element as extracted from the OTC database.",
        ),
        "effective_date": Column(
            "OTC:Effective Date",
            "The effective date element as extracted from the OTC database.",
        ),
        "received_date": Column(
            "OTC:Received Date",
            "The received date element as extracted from the OTC database.",
        ),
        "service_type_other_details": Column(
            "OTC:Service Type Other Details",
            "The service type other details element as extracted from the "
            "OTC database.",
        ),
        "traveline_region": Column(
            "Traveline Region",
            "The Traveline Region details element as extracted from the OTC database.",
        ),
        "local_authority_ui_lta": Column(
            "Local Transport Authority",
            "The Local Transport Authority element as extracted from the OTC database.",
        ),
    }
)

TIMETABLE_LINE_LEVEL_COLUMN_MAP = OrderedDict(
    {
        "registration_number": Column(
            "Registration:Registration Number",
            "The registration number element as extracted from the OTC database.",
        ),
        "service_number": Column(
            "Registration:Service Number",
            "The service number element as extracted from the OTC database.",
        ),
        "requires_attention": Column(
            "Requires Attention",
            "No: </br>"
            "Default state for correctly published services, will be “No” "
            "unless any of the logic below is met. </br></br>"
            "Yes: </br>"
            "Yes If OTC status = Registered and Scope Status = In scope and "
            "Seasonal Status ≠ Out of season and Published Status = Unpublished. </br>"
            "Yes if OTC status = Registered and Scope Status = In scope and "
            "Seasonal Status ≠ Out of season and Published Status = Published "
            "and Timeliness Status ≠ Up to date. ",
        ),
        "published_status": Column(
            "Published Status",
            "Published: Published to BODS by an Operator/Agent. </br></br>"
            "Unpublished: Not published to BODS by an Operator/Agent.",
        ),
        "otc_status": Column(
            "Registration Status",
            "Registered: Registered and not cancelled within the OTC "
            "database. </br></br>"
            "Unregistered: Not Registered within the OTC.",
        ),
        "scope_status": Column(
            "Scope Status",
            "In scope: Default status for services registered with the OTC and "
            "other enhanced partnerships. </br></br>"
            "Out of Scope: Service code has been marked as exempt by the DVSA "
            "or the BODS team.",
        ),
        "seasonal_status": Column(
            "Seasonal Status",
            "In season: Service code has been marked as seasonal by the "
            "operator or their agent and todays date falls within the "
            "relevant date range for that service code.  </br></br>"
            "Out of Season: Service code has been marked as seasonal by "
            "the operator or their agent and todays date falls outside "
            "the relevant date range for that service code.  </br></br>"
            "Not Seasonal: Default status for published or unpublished services"
            "to BODS. </br> Assumed Not seasonal unless service code has been marked "
            "with a date range within the seasonal services flow.",
        ),
        "staleness_status": Column(
            "Timeliness Status",
            "Up to date: Default status for service codes published to BODS. </br></br>"
            "Timeliness checks are evaluated in this order: </br></br>"
            "1) OTC Variation not published: </br>"
            "If 'XML:Last modified date' is earlier than 'Date OTC variation needs "
            "to be published' </br> and </br> 'Date OTC variation needs to be "
            "published'is earlier than today's date.</br> and </br>"
            "No associated data has been published. </br>"
            "NB there are two association methods: </br> Method 1: </br>"
            "Data for that service code has been updated within 70 days before "
            "the OTC variation effective date.</br> Method 2: </br>"
            "Data for that service code has been updated with a 'XML:Operating "
            "Period Start Date' which equals OTC variation effective date. </br></br>"
            "2) 42 day look ahead is incomplete: </br> If not out of date due to  "
            "'OTC variation not published' </br> and </br> 'XML:Operating Period "
            "End Date' is earlier than 'Date for complete 42 day look "
            "ahead'. </br></br>"
            "3) Service hasn't been updated within a year: </br> If not out of date "
            "due to '42 day lookahead is incomplete' or 'OTC variation not published'"
            "</br> and </br> 'Date at which data is 1 year old' is earlier than "
            "today's date.",
        ),
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS.",
        ),
        "dataset_id": Column(
            "Data set ID",
            "The internal BODS generated ID of the dataset "
            "that contains the data for this row.",
        ),
        "filename": Column(
            "XML:Filename",
            "The exact name of the file provided to BODS. This is usually "
            "generated by the publisher or their supplier.",
        ),
        "last_modified_date": Column(
            "XML:Last Modified Date",
            "Date of last modified file within the service codes dataset.",
        ),
        "operating_period_end_date": Column(
            "XML:Operating Period End Date",
            "The operating period end date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "effective_stale_date_from_otc_effective": Column(
            "Date Registration variation needs to be published",
            "Registration:Effective date from timetable data catalogue minus 42 days.",
        ),
        "date_42_day_look_ahead": Column(
            "Date for complete 42 day look ahead",
            "Today's date + 42 days.",
        ),
        "effective_stale_date_from_last_modified": Column(
            "Date when data is over 1 year old",
            "'XML:Last Modified date' from timetable data catalogue plus 12 months.",
        ),
        "effective_seasonal_start": Column(
            "Date seasonal service should be published",
            "If Seasonal Start Date is present, then Seasonal Start Date minus "
            "42 days, else null.",
        ),
        "seasonal_start": Column(
            "Seasonal Start Date",
            "If service has been assigned a date range from within the seasonal "
            "services flow, then take start date, else null.",
        ),
        "seasonal_end": Column(
            "Seasonal End Date",
            "If service has been assigned a date range from within the "
            "seasonal services flow, then take end date, else null.",
        ),
        "operator_name": Column(
            "Registration:Operator Name",
            "The operator name element as extracted from the OTC database.",
        ),
        "otc_licence_number": Column(
            "Registration:Licence Number",
            "The licence number element as extracted from the OTC database.",
        ),
        "service_type_description": Column(
            "Registration:Service Type Description",
            "The service type description element as extracted from the OTC database.",
        ),
        "variation_number": Column(
            "Registration:Variation Number",
            "The variation number element as extracted from the OTC database.",
        ),
        "expiry_date": Column(
            "Registration:Expiry Date",
            "The expiry date element as extracted from the OTC database.",
        ),
        "effective_date": Column(
            "Registration:Effective Date",
            "The effective date element as extracted from the OTC database.",
        ),
        "received_date": Column(
            "Registration:Received Date",
            "The received date element as extracted from the OTC database.",
        ),
        "traveline_region": Column(
            "Traveline Region",
            "The Traveline Region details element as extracted from the OTC database.",
        ),
        "local_authority_ui_lta": Column(
            "Local Transport Authority",
            "The Local Transport Authority element as extracted from the OTC database.",
        ),
    }
)

TIMETABLE_COMPLIANCE_REPORT_COLUMN_MAP = OrderedDict(
    {
        "registration_number": Column(
            "Registration:Registration Number",
            "The registration number element as extracted from the OTC database.",
        ),
        "service_number": Column(
            "Registration:Service Number",
            "The service number element as extracted from the OTC database.",
        ),
        "otc_status": Column(
            "Registration Status",
            "Registered: Registered and not cancelled within the OTC "
            "database. </br></br>"
            "Unregistered: Not Registered within the OTC.",
        ),
        "scope_status": Column(
            "Scope Status",
            "In scope: Default status for services registered with the OTC and "
            "other enhanced partnerships. </br></br>"
            "Out of Scope: Service code has been marked as exempt by the DVSA "
            "or the BODS team.",
        ),
        "seasonal_status": Column(
            "Seasonal Status",
            "In season: Service code has been marked as seasonal by the "
            "operator or their agent and todays date falls within the "
            "relevant date range for that service code.  </br></br>"
            "Out of Season: Service code has been marked as seasonal by "
            "the operator or their agent and todays date falls outside "
            "the relevant date range for that service code.  </br></br>"
            "Not Seasonal: Default status for published or unpublished services"
            "to BODS. </br> Assumed Not seasonal unless service code has been marked "
            "with a date range within the seasonal services flow.",
        ),
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS.",
        ),
        "overall_requires_attention": Column(
            "Requires Attention",
            "Overall Requires Attention.",
        ),
        "requires_attention": Column(
            "Timetables requires attention",
            "No: </br>"
            "Default state for correctly published services, will be “No” "
            "unless any of the logic below is met. </br></br>"
            "Yes: </br>"
            "Yes If OTC status = Registered and Scope Status = In scope and "
            "Seasonal Status ≠ Out of season and Published Status = Unpublished. </br>"
            "Yes if OTC status = Registered and Scope Status = In scope and "
            "Seasonal Status ≠ Out of season and Published Status = Published "
            "and Timeliness Status ≠ Up to date. ",
        ),
        "published_status": Column(
            "Timetables Published Status",
            "Published: Published to BODS by an Operator/Agent. </br></br>"
            "Unpublished: Not published to BODS by an Operator/Agent.",
        ),
        "staleness_status": Column(
            "Timetables Timeliness Status",
            "Up to date: Default status for service codes published to BODS. </br></br>"
            "Timeliness checks are evaluated in this order: </br></br>"
            "1) OTC Variation not published: </br>"
            "If 'XML:Last modified date' is earlier than 'Date OTC variation needs "
            "to be published' </br> and </br> 'Date OTC variation needs to be "
            "published'is earlier than today's date.</br> and </br>"
            "No associated data has been published. </br>"
            "NB there are two association methods: </br> Method 1: </br>"
            "Data for that service code has been updated within 70 days before "
            "the OTC variation effective date.</br> Method 2: </br>"
            "Data for that service code has been updated with a 'XML:Operating "
            "Period Start Date' which equals OTC variation effective date. </br></br>"
            "2) 42 day look ahead is incomplete: </br> If not out of date due to  "
            "'OTC variation not published' </br> and </br> 'XML:Operating Period "
            "End Date' is earlier than 'Date for complete 42 day look "
            "ahead'. </br></br>"
            "3) Service hasn't been updated within a year: </br> If not out of date "
            "due to '42 day lookahead is incomplete' or 'OTC variation not published'"
            "</br> and </br> 'Date at which data is 1 year old' is earlier than "
            "today's date.",
        ),
        "critical_dq_issues": Column(
            "Timetables critical DQ issues",
            "Under maintenance.",
        ),
        "avl_requires_attention": Column(
            "AVL requires attention",
            "AVL requires attention.",
        ),
        "avl_published_status": Column(
            "AVL Published Status",
            "AVL Published Status.",
        ),
        "error_in_avl_to_timetable_matching": Column(
            "Error in AVL to Timetable Matching",
            "Error in AVL to Timetable Matching.",
        ),
        "fares_requires_attention": Column(
            "Fares requires attention",
            "Under maintenance.",
        ),
        "fares_published_status": Column(
            "Fares Published Status",
            "Under maintenance.",
        ),
        "fares_timeliness_status": Column(
            "Fares Timeliness Status",
            "Under maintenance.",
        ),
        "fares_compliance_status": Column(
            "Fares Compliance Status",
            "Under maintenance.",
        ),
        "dataset_id": Column(
            "Timetables Data set ID",
            "The internal BODS generated ID of the dataset "
            "that contains the data for this row.",
        ),
        "filename": Column(
            "TXC:Filename",
            "The exact name of the file provided to BODS. This is usually "
            "generated by the publisher or their supplier.",
        ),
        "national_operator_code": Column(
            "TXC:NOC",
            "The National Operator Code(s) as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "last_modified_date": Column(
            "TXC:Last Modified Date",
            "Date of last modified file within the service codes dataset.",
        ),
        "effective_stale_date_from_last_modified": Column(
            "Date when timetable data is over 1 year old",
            "'XML:Last Modified date' from timetable data catalogue plus 12 months.",
        ),
        "operating_period_end_date": Column(
            "TXC:Operating Period End Date",
            "The operating period end date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "fares_dataset_id": Column(
            "Fares Data set ID",
            "Under maintenance.",
        ),
        "fares_filename": Column(
            "NETEX:Filename",
            "Under maintenance.",
        ),
        "fares_last_modified_date": Column(
            "NETEX:Last Modified Date",
            "Under maintenance.",
        ),
        "fares_effective_stale_date_from_last_modified": Column(
            "Date when fares data is over 1 year old",
            "Under maintenance.",
        ),
        "fares_operating_period_end_date": Column(
            "NETEX:Operating Period End Date",
            "Under maintenance.",
        ),
        "effective_stale_date_from_otc_effective": Column(
            "Date Registration variation needs to be published",
            "Registration:Effective date from timetable data catalogue minus 42 days.",
        ),
        "date_42_day_look_ahead": Column(
            "Date for complete 42 day look ahead",
            "Today's date + 42 days.",
        ),
        "effective_seasonal_start": Column(
            "Date seasonal service should be published",
            "If Seasonal Start Date is present, then Seasonal Start Date minus "
            "42 days, else null.",
        ),
        "seasonal_start": Column(
            "Seasonal Start Date",
            "If service has been assigned a date range from within the seasonal "
            "services flow, then take start date, else null.",
        ),
        "seasonal_end": Column(
            "Seasonal End Date",
            "If service has been assigned a date range from within the "
            "seasonal services flow, then take end date, else null.",
        ),
        "operator_name": Column(
            "Registration:Operator Name",
            "The operator name element as extracted from the OTC database.",
        ),
        "otc_licence_number": Column(
            "Registration:Licence Number",
            "The licence number element as extracted from the OTC database.",
        ),
        "service_type_description": Column(
            "Registration:Service Type Description",
            "The service type description element as extracted from the OTC database.",
        ),
        "variation_number": Column(
            "Registration:Variation Number",
            "The variation number element as extracted from the OTC database.",
        ),
        "expiry_date": Column(
            "Registration:Expiry Date",
            "The expiry date element as extracted from the OTC database.",
        ),
        "effective_date": Column(
            "Registration:Effective Date",
            "The effective date element as extracted from the OTC database.",
        ),
        "received_date": Column(
            "Registration:Received Date",
            "The received date element as extracted from the OTC database.",
        ),
        "traveline_region": Column(
            "Traveline Region",
            "The Traveline Region details element as extracted from the OTC database.",
        ),
        "local_authority_ui_lta": Column(
            "Local Transport Authority",
            "The Local Transport Authority element as extracted from the OTC database.",
        ),
    }
)


def add_operator_name(row: Series) -> str:
    if row["organisation_name"] is None or pd.isna(row["organisation_name"]):
        otc_licence_number = row["otc_licence_number"]
        operator_name = Organisation.objects.get_organisation_name(otc_licence_number)

        if not operator_name:
            return "Organisation not yet created"
        else:
            return operator_name
    else:
        return row["organisation_name"]


def scope_status(row, exempted_reg_numbers):
    """
    Column “Scope” for a service
    A service should be deemed “in scope” if:
    Registered with OTC or WECA and has not been marked out of scope by the DVSA.
    If at least one of the Traveline Region values for that row is mapped to England.
    Args:
        row (df): Dataframe row
        exempted_reg_numbers (array): array of dataframe with registration number

    Returns:
        df: df
    """
    is_exempted = row["registration_number"] in exempted_reg_numbers
    traveline_regions = row["traveline_region"].split("|")
    isin_english_region = list(set(ENGLISH_TRAVELINE_REGIONS) & set(traveline_regions))

    row["scope_status"] = OTC_SCOPE_STATUS_OUT_OF_SCOPE
    if (
        row["otc_status"] == OTC_STATUS_REGISTERED
        and not is_exempted
        and isin_english_region
    ):
        row["scope_status"] = OTC_SCOPE_STATUS_IN_SCOPE

    return row


def traveline_regions(row, traveline_regions_dict):
    """
    Traveline region need to mapped with Value metioned in TravelineRegions

    Args:
        row (df): df row
        traveline_regions_dict (dict): Dictionary of tavelineregion key value map

    Returns:
        df: modified row of df
    """
    traveline_regions = row["traveline_region"].split("|")
    travelines = [
        traveline_regions_dict.get(region, region)
        for region in traveline_regions
        if region != "None"
    ]
    if travelines:
        row["traveline_region"] = "|".join(map(str, travelines))
    return row


def add_traveline_regions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Traveline Regions short form is fetched from DB and
    it need to be replaced by label assigned in TravelineRegions

    Args:
        row (df): Merged df

    Returns:
        df: modified row of df
    """
    traveline_regions_dict = {
        region_code: pretty_name_region_code
        for region_code, pretty_name_region_code in TravelineRegions.choices
    }
    return df.apply(traveline_regions, args=[traveline_regions_dict], axis=1)


def add_status_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Status columns of published, otc and scopes will be modified

    Args:
        df (pd.DataFrame): Merged df

    Returns:
        pd.DataFrame: Modified df
    """
    exists_in_bods = np.invert(pd.isna(df["dataset_id"]))
    exists_in_otc = np.invert(pd.isna(df["otc_licence_number"]))
    exempted_reg_numbers = (
        ServiceCodeExemption.objects.add_registration_number()
        .values_list("registration_number", flat=True)
        .all()
    )
    df["published_status"] = np.where(exists_in_bods, "Published", "Unpublished")
    df["otc_status"] = np.where(
        exists_in_otc, OTC_STATUS_REGISTERED, OTC_STATUS_UNREGISTERED
    )
    df["traveline_region"] = df["traveline_region"].fillna("").astype(str)
    df = df.apply(scope_status, args=[exempted_reg_numbers], axis=1)
    return df


def add_seasonal_status(df: pd.DataFrame, today: datetime.date) -> pd.DataFrame:
    seasonal_services_df = pd.DataFrame.from_records(
        SeasonalService.objects.add_registration_number().values(
            *SEASONAL_SERVICE_COLUMNS
        )
    )
    if seasonal_services_df.empty:
        df["seasonal_start"] = pd.NaT
        df["seasonal_end"] = pd.NaT
        df["seasonal_status"] = "Not Seasonal"
        return df

    seasonal_services_df.rename(
        columns={"start": "seasonal_start", "end": "seasonal_end"}, inplace=True
    )
    annotated_df = pd.merge(
        df, seasonal_services_df, on="registration_number", how="left"
    )

    not_seasonal = pd.isna(annotated_df["seasonal_start"])
    in_season = (annotated_df["seasonal_start"] <= today) & (
        annotated_df["seasonal_end"] >= today
    )
    annotated_df["seasonal_status"] = np.select(
        condlist=[not_seasonal, in_season],
        choicelist=["Not Seasonal", "In Season"],
        default="Out of Season",
    )

    return annotated_df


def defer_one_year(d):
    return d if pd.isna(d) else (d + pd.DateOffset(years=1)).date()


def add_staleness_metrics(df: pd.DataFrame, today: datetime.date) -> pd.DataFrame:
    today = np.datetime64(today)
    df["last_modified_date"] = df["modification_datetime"].dt.date
    df["effective_last_modified_date"] = df["last_modified_date"]

    df["effective_seasonal_start"] = df["seasonal_start"] - pd.Timedelta(days=42)

    df["effective_stale_date_from_end_date"] = df[
        "operating_period_end_date"
    ] - pd.Timedelta(days=42)

    df["effective_stale_date_from_last_modified"] = df[
        "effective_last_modified_date"
    ].apply(defer_one_year)
    df["effective_stale_date_from_otc_effective"] = df["effective_date"] - pd.Timedelta(
        days=42
    )
    df["association_date_otc_effective_date"] = df["effective_date"] - pd.Timedelta(
        days=70
    )

    df["last_modified_lt_effective_stale_date_otc"] = (
        df["last_modified_date"] < df["effective_stale_date_from_otc_effective"]
    )

    df["today_lt_effective_stale_date_otc"] = (
        today < df["effective_stale_date_from_otc_effective"]
    )

    df["is_data_associated"] = (
        df["last_modified_date"] >= df["association_date_otc_effective_date"]
    ) | (df["operating_period_start_date"] == df["effective_date"])

    """
    today_lt_effective_stale_date_otc is True if effective_stale_date_from_otc_effective
    is less than today where
    effective_stale_date_from_otc_effective = effective_date - 42 days.
    is_data_associated is set to true if operating period start date equals
    effective date or last modified date is greater than (effective_date - 70 days)
    """
    not_stale_otc = df["today_lt_effective_stale_date_otc"] | df["is_data_associated"]
    staleness_otc = ~not_stale_otc

    forty_two_days_from_today = today + np.timedelta64(42, "D")

    staleness_42_day_look_ahead = (
        (staleness_otc == False)
        & pd.notna(df["operating_period_end_date"])
        & (df["operating_period_end_date"] < forty_two_days_from_today)
    )

    """
    effective_stale_date_from_end_date = effective_date - 42 days
    effective_stale_date_from_last_modified = last_modified_date - 365 days (or 1 year)
    """
    staleness_12_months = (
        (staleness_otc == False)
        & (staleness_42_day_look_ahead == False)
        & (
            pd.to_datetime(df["last_modified_date"]).values.astype("datetime64")
            + np.timedelta64(365, "D")
            <= today
        )
    )

    df["staleness_status"] = np.select(
        condlist=[staleness_42_day_look_ahead, staleness_12_months, staleness_otc],
        choicelist=[
            "42 day look ahead is incomplete",
            "Service hasn't been updated within a year",
            "OTC variation not published",
        ],
        default="Up to date",
    )
    df["date_42_day_look_ahead"] = today + 42

    return df


def add_timetables_requires_attention_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Logic for Requires Attention:
    Yes if all of these are true:
        Scope Status = In scope AND
        Seasonal Status = Not Seasonal or In Season AND
        Registration Status = Registered

        AND

        Published Status = Unpublished OR
        Timeliness Status != Up to Date OR
        Critical DQ Issues = Yes
    No if all of these are true:
        Scope Status = Out of Scope OR
        Seasonal Status = Out of Season

        Scope Status = In scope AND
        Seasonal Status = Not Seasonal or In Season AND
        Registration Status = Registered AND
        Published Status = Published AND
        Timeliness Status = Up to Date AND
        Critical DQ Issues = No
    """
    timetables_requires_attention_unpublished = (
        (df["scope_status"] == OTC_SCOPE_STATUS_IN_SCOPE)
        & (
            (df["seasonal_status"] == "Not Seasonal")
            | (df["seasonal_status"] == "In Season")
        )
        & (df["otc_status"] == "Registered")
    ) & (
        (df["published_status"] == "Unpublished")
        | (df["staleness_status"] != "Up to date")
        | (df["critical_dq_issues"] == "Yes")
    )

    df["requires_attention"] = np.where(
        timetables_requires_attention_unpublished, "Yes", "No"
    )

    return df


def add_critical_dq_issue_status(x, dq_issue_services: List[tuple]) -> str:
    if (x["service_code"], x["line_name_unnested"]) in dq_issue_services:
        return "Yes"
    return "No"


def add_requires_attention_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Logic for Requires Attention:
    Yes if all of these are true:
        OTC status = Registered
        Scope Status = In scope
        Seasonal Status = Not Seasonal or In Season
        Published Status = Unpublished
    Yes if all these are true:
        OTC status = Registered
        Scope Status = In scope
        Seasonal Status = Not Seasonal or In Season
        Published Status = Published
        Timeliness Status ≠ Up to date
    """
    requires_attention_unpublished = (
        (df["otc_status"] == "Registered")
        & (df["scope_status"] == OTC_SCOPE_STATUS_IN_SCOPE)
        & (
            (df["seasonal_status"] == "Not Seasonal")
            | (df["seasonal_status"] == "In Season")
        )
        & (df["published_status"] == "Unpublished")
    )

    requires_attention_published = (
        (df["otc_status"] == "Registered")
        & (df["scope_status"] == OTC_SCOPE_STATUS_IN_SCOPE)
        & (
            (df["seasonal_status"] == "Not Seasonal")
            | (df["seasonal_status"] == "In Season")
        )
        & (df["published_status"] == "Published")
        & (df["staleness_status"] != "Up to date")
    )
    df["requires_attention"] = np.where(
        (requires_attention_unpublished) | (requires_attention_published), "Yes", "No"
    )
    return df


def cast_boolean_to_string(value: Optional[bool]) -> str:
    if value:
        return "YES"
    elif value is None:
        return ""
    else:
        return "NO"


def add_under_maintenance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds string value to specific columns that are under maintenance.

    Args:
        df (pd.DataFrame): Dataframe

    Returns:
        pd.DataFrame: Updated dataframe
    """
    df["fares_requires_attention"] = "Under maintenance"
    df["fares_published_status"] = "Under maintenance"
    df["fares_timeliness_status"] = "Under maintenance"
    df["fares_compliance_status"] = "Under maintenance"
    df["fares_dataset_id"] = "Under maintenance"
    df["fares_filename"] = "Under maintenance"
    df["fares_last_modified_date"] = "Under maintenance"
    df["fares_effective_stale_date_from_last_modified"] = "Under maintenance"
    df["fares_operating_period_end_date"] = "Under maintenance"

    return df


def add_avl_published_status(row: Series, synced_in_last_month) -> str:
    """
    Returns value for 'AVL Published Status' column.

    Args:
        row (Series): Row of the dataframe
        synced_in_last_month: Records from ABODS API

    Returns:
        str: Yes or No for 'AVL Published Status' column
    """
    line_name = row["service_number"]
    operator_ref = row["national_operator_code"]

    if f"{line_name}__{operator_ref}" in synced_in_last_month:
        return "Yes"
    return "No"


def add_error_in_avl_to_timetable_matching(row: Series) -> str:
    """
    Returns value for 'Error in AVL to Timetable Matching' column.

    Args:
        row (Series): Row of the dataframe

    Returns:
        str: Yes or No for 'Error in AVL to Timetable Matching' column
    """
    line_name = str(row["service_number"])
    operator_ref = row["national_operator_code"]
    uncounted_activity_df = get_vehicle_activity_operatorref_linename()

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


def add_avl_requires_attention(row: Series) -> str:
    """
    Returns value for 'AVL requires attention' column based on the following logic:

    If both 'AVL Published Status' equal to Yes
    and 'Error in AVL to Timetable Matching' equal to No,
    then 'AVL requires attention' = No.
    else
    the value 'AVL requires attention' = Yes.

    Args:
        row (Series): Row of the dataframe

    Returns:
        str: Yes or No for 'AVL requires attention' column
    """
    avl_published_status = row["avl_published_status"]
    error_in_avl_to_timetable_matching = row["error_in_avl_to_timetable_matching"]

    if (avl_published_status == "Yes") and (error_in_avl_to_timetable_matching == "No"):
        return "No"
    return "Yes"


def add_overall_requires_attention(row: Series) -> str:
    """
    Updates value for 'Requires attention' column based on the following logic:

    If 'Scope Status' = Out of Scope OR 'Seasonal Status' = Out of Season,
    then 'Requires attention' = No.
    If 'Timetables requires attention' = No AND 'AVL requires attention' = No,
    then 'Requires attention' = No.
    If 'Timetables requires attention' = Yes OR 'AVL requires attention' = Yes,
    then 'Requires attention' = Yes.

    Args:
        row (Series): Row of the dataframe

    Returns:
        str: Value for the column
    """
    exempted = row["scope_status"]
    seasonal_service = row["seasonal_status"]
    timetable_requires_attention = row["requires_attention"]
    avl_requires_attention = row["avl_requires_attention"]

    if (exempted == "Out of Scope") or (seasonal_service == "Out of Season"):
        return "No"
    if (timetable_requires_attention == "No") and (avl_requires_attention == "No"):
        return "No"
    return "Yes"


def _get_timetable_catalogue_dataframe() -> pd.DataFrame:
    today = datetime.date.today()

    txc_df = pd.DataFrame.from_records(
        TXCFileAttributes.objects.get_active_txc_files().values(*TXC_COLUMNS)
    )
    otc_df = pd.DataFrame.from_records(
        OTCService.objects.add_timetable_data_annotations().values(*OTC_COLUMNS)
    )
    if txc_df.empty or otc_df.empty:
        raise EmptyDataFrame()

    castings = (
        ("dataset_id", "Int64"),
        ("revision_number", "Int64"),
        ("public_use", "boolean"),
        ("variation_number", "Int64"),
        ("otc_operator_id", "Int64"),
    )

    merged = pd.merge(otc_df, txc_df, on="service_code", how="outer")

    for field, type_ in castings:
        merged[field] = merged[field].astype(type_)

    merged.sort_values("dataset_id", inplace=True)
    merged["organisation_name"] = merged.apply(lambda x: add_operator_name(x), axis=1)
    merged = add_status_columns(merged)
    merged = add_seasonal_status(merged, today)
    merged = add_staleness_metrics(merged, today)
    merged = add_requires_attention_column(merged)
    merged = add_traveline_regions(merged)

    rename_map = {
        old_name: column_tuple.field_name
        for old_name, column_tuple in TIMETABLE_COLUMN_MAP.items()
    }
    merged = merged[TIMETABLE_COLUMN_MAP.keys()].rename(columns=rename_map)
    return merged


def _get_timetable_line_level_catalogue_dataframe() -> pd.DataFrame:
    today = datetime.date.today()

    txc_df = pd.DataFrame.from_records(
        TXCFileAttributes.objects.get_active_txc_files_line_level().values(
            *TXC_LINE_LEVEL_COLUMNS
        )
    )
    otc_df = pd.DataFrame.from_records(
        OTCService.objects.add_timetable_data_annotations().values(*OTC_COLUMNS)
    )
    if txc_df.empty or otc_df.empty:
        raise EmptyDataFrame()

    otc_df["service_number"] = otc_df["service_number"].str.split("|")
    otc_df = otc_df.explode("service_number")

    castings = (
        ("dataset_id", "Int64"),
        ("revision_number", "Int64"),
        ("public_use", "boolean"),
        ("variation_number", "Int64"),
        ("otc_operator_id", "Int64"),
    )

    merged = pd.merge(
        otc_df,
        txc_df,
        left_on=["service_code", "service_number"],
        right_on=["service_code", "line_name_unnested"],
        how="outer",
    )

    for field, type_ in castings:
        merged[field] = merged[field].astype(type_)

    merged.sort_values("dataset_id", inplace=True)
    merged["organisation_name"] = merged.apply(lambda x: add_operator_name(x), axis=1)
    merged = add_status_columns(merged)
    merged = add_seasonal_status(merged, today)
    merged = add_staleness_metrics(merged, today)
    merged = add_requires_attention_column(merged)
    merged = add_traveline_regions(merged)

    merged = merged[merged["otc_status"] == OTC_STATUS_REGISTERED]

    rename_map = {
        old_name: column_tuple.field_name
        for old_name, column_tuple in TIMETABLE_LINE_LEVEL_COLUMN_MAP.items()
    }
    merged = merged[TIMETABLE_LINE_LEVEL_COLUMN_MAP.keys()].rename(columns=rename_map)
    return merged


def _get_timetable_compliance_report_dataframe() -> pd.DataFrame:
    today = datetime.date.today()
    abods_registry = AbodsRegistery()
    synced_in_last_month = abods_registry.records()

    txc_service_map = {}
    txc_attributes = TXCFileAttributes.objects.get_active_txc_files_line_level()
    txc_df = pd.DataFrame.from_records(txc_attributes.values(*TXC_LINE_LEVEL_COLUMNS))
    otc_df = pd.DataFrame.from_records(
        OTCService.objects.add_timetable_data_annotations().values(*OTC_COLUMNS)
    )
    if txc_df.empty or otc_df.empty:
        raise EmptyDataFrame()

    otc_df["service_number"] = otc_df["service_number"].str.split("|")
    otc_df = otc_df.explode("service_number")
    dq_require_attention_active = flag_is_active("", "dq_require_attention")
    if dq_require_attention_active:
        dq_critical_observations_map = (
            get_dq_critical_observation_services_map_from_dataframe(txc_df)
        )

    castings = (
        ("dataset_id", "Int64"),
        ("revision_id", "Int64"),
        ("revision_number", "Int64"),
        ("public_use", "boolean"),
        ("variation_number", "Int64"),
        ("otc_operator_id", "Int64"),
    )

    is_fares_require_attention_active = flag_is_active(
        "", "fares_require_attention_active"
    )
    if is_fares_require_attention_active:
        for txc_attribute in txc_attributes:
            txc_service_map[txc_attribute.service_code] = txc_attribute
        fares_df = get_fares_dataset_map(txc_map=txc_service_map)
        fares_df["valid_to"] = fares_df["valid_to"].dt.date
        fares_df["fares_timeliness_status"] = fares_df.apply(
            lambda x: is_fares_stale(x.valid_to, x.last_updated_date), axis=1
        )
        fares_df["fares_effective_stale_date_from_last_modified"] = fares_df[
            "last_updated_date"
        ] + pd.Timedelta(days=365)
        fares_df.rename(
            columns={
                "is_fares_compliant": "fares_compliance_status",
                "xml_file_name": "fares_filename",
                "last_updated_date": "fares_last_modified_date",
                "valid_to": "fares_operating_period_end_date",
                "dataset_id": "fares_dataset_id",
            },
            inplace=True,
        )
        txc_df = pd.merge(
            txc_df,
            fares_df,
            left_on=["national_operator_code", "line_name_unnested"],
            right_on=["national_operator_code", "line_name"],
            how="outer",
        )

    merged = pd.merge(
        otc_df,
        txc_df,
        left_on=["service_code", "service_number"],
        right_on=["service_code", "line_name_unnested"],
        how="outer",
    )

    for field, type_ in castings:
        merged[field] = merged[field].astype(type_)

    merged.sort_values("dataset_id", inplace=True)
    merged["organisation_name"] = merged.apply(lambda x: add_operator_name(x), axis=1)
    merged = add_status_columns(merged)
    merged = add_seasonal_status(merged, today)
    merged = add_staleness_metrics(merged, today)
    if dq_require_attention_active:
        merged["critical_dq_issues"] = merged.apply(
            lambda x: add_critical_dq_issue_status(x, dq_critical_observations_map),
            axis=1,
        )
    else:
        merged["critical_dq_issues"] = UNDER_MAINTENANCE
    merged = add_timetables_requires_attention_column(merged)
    merged = add_traveline_regions(merged)
    if not is_fares_require_attention_active:
        merged = add_under_maintenance_columns(merged)

    merged["avl_published_status"] = merged.apply(
        lambda x: add_avl_published_status(x, synced_in_last_month), axis=1
    )
    merged["error_in_avl_to_timetable_matching"] = merged.apply(
        lambda x: add_error_in_avl_to_timetable_matching(x), axis=1
    )
    merged["avl_requires_attention"] = merged.apply(
        lambda x: add_avl_requires_attention(x), axis=1
    )
    merged["overall_requires_attention"] = merged.apply(
        lambda x: add_overall_requires_attention(x), axis=1
    )

    merged = merged[merged["otc_status"] == OTC_STATUS_REGISTERED]

    if is_fares_require_attention_active:
        merged["fares_published_status"] = txc_df["fares_filename"].apply(
            lambda x: "Yes" if pd.notna(x) and x.strip() != "" else "No"
        )
        merged["fares_requires_attention"] = np.where(
            (merged["fares_published_status"] == "Yes")
            & (merged["fares_timeliness_status"] == "Yes")
            & (merged["fares_compliance_status"] == "Yes"),
            "Yes",
            "No",
        )
        merged["overall_requires_attention"] = np.where(
            (merged["fares_published_status"] == "Yes")
            & (merged["requires_attention"] == "Yes")
            & (merged["avl_requires_attention"] == "Yes"),
            "Yes",
            "No",
        )

    rename_map = {
        old_name: column_tuple.field_name
        for old_name, column_tuple in TIMETABLE_COMPLIANCE_REPORT_COLUMN_MAP.items()
    }
    merged = merged[TIMETABLE_COMPLIANCE_REPORT_COLUMN_MAP.keys()].rename(
        columns=rename_map
    )
    return merged


def get_timetable_catalogue_csv():
    return _get_timetable_catalogue_dataframe().to_csv(index=False)


def get_line_level_timetable_catalogue_csv():
    return _get_timetable_line_level_catalogue_dataframe().to_csv(index=False)


def get_timetable_compliance_report():
    return _get_timetable_compliance_report_dataframe().to_csv(index=False)
