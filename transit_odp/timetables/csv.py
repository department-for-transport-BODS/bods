import datetime
from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd
from pandas import Series

from transit_odp.common.collections import Column
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.models import (
    Organisation,
    SeasonalService,
    ServiceCodeExemption,
    TXCFileAttributes,
)
from transit_odp.otc.models import Service as OTCService

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
    "local_authority_name",
    "local_authority_ui_lta",
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
            "OTC:Traveline Region",
            "The Traveline Region details element as extracted from the OTC database.",
        ),
        "local_authority_name": Column(
            "OTC:Local Authority",
            "The Local Authority element as extracted from the OTC database.",
        ),
        "local_authority_ui_lta": Column(
            "OTC:UI LTA",
            "The UI LTA element as extracted from the OTC database.",
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


def add_status_columns(df: pd.DataFrame) -> pd.DataFrame:
    exists_in_bods = np.invert(pd.isna(df["dataset_id"]))
    exists_in_otc = np.invert(pd.isna(df["otc_licence_number"]))
    exempted_reg_numbers = (
        ServiceCodeExemption.objects.add_registration_number()
        .values_list("registration_number", flat=True)
        .all()
    )
    registration_number_exempted = df["registration_number"].isin(exempted_reg_numbers)

    df["published_status"] = np.where(exists_in_bods, "Published", "Unpublished")
    df["otc_status"] = np.where(exists_in_otc, "Registered", "Unregistered")
    df["scope_status"] = np.where(
        registration_number_exempted, "Out of Scope", "In Scope"
    )

    traline_scope = df["traveline_region"].isin(
        ["EA", "EM", "NE", "NW", "SE", "SW", "WM", "Y"]
    )

    if not traline_scope.empty:
        """
        If service belongs to a UI LTA that is in an English Traveline Region: EA, EM, NE, NW, SE, SW, WM, Y
        Then in scope unless already out of scope from DfT admin portal (Need to add this condition)
        """
        df["scope_status"] = np.where(
            traline_scope,
            "In Scope",
            "Out of Scope",
        )
        ui_lta_scope = df["traveline_region"].isin(["Null", "S", "W", "L"])
        """
            If service does not belong to a UI LTA that is in an English Traveline Region: Null, S, W, L
            Then out of scope.
        """
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
        (staleness_otc is False)
        & pd.notna(df["operating_period_end_date"])
        & (df["operating_period_end_date"] < forty_two_days_from_today)
    )

    """
    effective_stale_date_from_end_date = effective_date - 42 days
    effective_stale_date_from_last_modified = last_modified_date - 365 days (or 1 year)
    """
    staleness_12_months = (
        (staleness_otc is False)
        & (staleness_42_day_look_ahead is False)
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


def add_requires_attention_column(
    df: pd.DataFrame, today: datetime.date
) -> pd.DataFrame:
    requires_attention = (
        (df["scope_status"] == "In Scope")
        & (df["seasonal_status"] != "Out of Season")
        & (
            (df["staleness_status"] != "Up to date")
            | (
                (df["published_status"] == "Unpublished")
                & (df["otc_status"] == "Registered")
            )
        )
    )
    df["requires_attention"] = np.where(requires_attention, "Yes", "No")
    return df


def cast_boolean_to_string(value: Optional[bool]) -> str:
    if value:
        return "YES"
    elif value is None:
        return ""
    else:
        return "NO"


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
    merged = add_requires_attention_column(merged, today)

    rename_map = {
        old_name: column_tuple.field_name
        for old_name, column_tuple in TIMETABLE_COLUMN_MAP.items()
    }
    merged = merged[TIMETABLE_COLUMN_MAP.keys()].rename(columns=rename_map)
    return merged


def get_timetable_catalogue_csv():
    return _get_timetable_catalogue_dataframe().to_csv(index=False)
