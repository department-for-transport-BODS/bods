import datetime
from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd
from pandas import Series

from transit_odp.common.collections import Column
from transit_odp.common.utils import round_down
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
    "score",
    "bods_compliant",
    "last_updated_date",
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
)

SEASONAL_SERVICE_COLUMNS = ("registration_number", "start", "end")

TIMETABLE_COLUMN_MAP = OrderedDict(
    {
        "requires_attention": Column(
            "Requires Attention",
            "No: Default state for correctly published services, will be “No” "
            "unless any of the logic below is met. "
            "Yes: Yes IF Staleness Status does not equal “Not Stale”. "
            "Yes IF Published Status = Unpublished and OTC status = Registered "
            "and Scope Status = In scope and Seasonal Status = Not Seasonal. "
            "Yes IF Published Status = Unpublished and OTC status = Registered "
            "and Scope Status = In scope and Seasonal Status = In season.",
        ),
        "published_status": Column(
            "Published Status",
            "Published: Published to BODS by an Operator/Agent. "
            "Unpublished: Not published to BODS by an Operator/Agent.",
        ),
        "otc_status": Column(
            "OTC Status",
            "Registered: Registered and not cancelled within the OTC database. "
            "Unregistered: Not Registered within the OTC.",
        ),
        "scope_status": Column(
            "Scope Status",
            "In scope: Default status for published or unpublished services to "
            "BODS. Assumed in scope unless marked as exempt in the service "
            "code exemption flow. "
            "Out of Scope: Service code has been marked as exempt by the DVSA "
            "in the service code exemption flow.",
        ),
        "seasonal_status": Column(
            "Seasonal Status",
            "In season: Service code has been marked with a date range within "
            "the seasonal services flow and the date from which the file is "
            "created falls within the date range for that service code. "
            "Out of Season: Service code has been marked with a date range "
            "within the seasonal services flow and the date from which the "
            "file is created falls outside the date range for that service "
            "code. "
            "Not Seasonal: Default status for published or unpublished "
            "services to BODS. Assumed Not seasonal unless service code has "
            "been marked with a date range within the seasonal services flow.",
        ),
        "staleness_status": Column(
            "Staleness Status",
            "Not Stale: Default status for service codes published to BODS. </br></br>"
            "Stale - 42 day look ahead: If stateness status is not OTC Variation "
            "and operating period end date is present and less than today’s date"
            "plus 42 days.  </br></br>"
            "Stale - 12 months old: If 'Effective stale date due to effective "
            "last modified' date is sooner than 'Effective stale date due to "
            "end date' (if present) and today’s date from which the file is "
            "created equals or passes 'Effective stale date due to effective "
            "last modified date' and Last modified date < 'Effective stale date "
            "due to OTC effective date' = FALSE. </br></br>"
            "Stale - OTC Variation: If Last modified date < 'Effective stale date "
            "due to OTC effective date' = TRUE and Today’s date greater"
            " than or equal to 'Effective stale date due to OTC effective date'.",
        ),
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS.",
        ),
        "dataset_id": Column(
            "Dataset ID",
            "The internal BODS generated ID of the dataset "
            "that contains the data for this row.",
        ),
        "score": Column(
            "DQ Score",
            "The DQ score assigned to the publisher’s data set as a result of "
            "the additional data quality checks done on timetables data on "
            "BODS.",
        ),
        "bods_compliant": Column(
            "BODS Compliant",
            "The validation status and format of timetables data.",
        ),
        "last_updated_date": Column(
            "Last Updated Date",
            "The date that the data set/feed was last updated on BODS",
        ),
        "last_modified_date": Column(
            "Last Modified Date",
            "Date of last modified file within the service codes dataset.",
        ),
        "effective_last_modified_date": Column(
            "Effective Last Modified Date",
            "Equal to Last Modified Date.",
        ),
        "filename": Column(
            "XML Filename",
            "The exact name of the file provided to BODS. This is usually generated"
            " by the publisher or their supplier",
        ),
        "licence_number": Column(
            "Data set Licence Number",
            "The License number(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "national_operator_code": Column(
            "National Operator Code",
            "The National Operator Code(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "service_code": Column(
            "Data set Service Code",
            "The ServiceCode(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "public_use": Column(
            "Public Use Flag",
            "The Public Use Flag element as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "operating_period_start_date": Column(
            "Operating Period Start Date",
            "The operating period start date as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "operating_period_end_date": Column(
            "Operating Period End Date",
            "The operating period end date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "effective_stale_date_from_end_date": Column(
            "Effective stale date due to end date",
            "If end date exists within the timetable file "
            "Then take end date from TransXChange file minus 42 days.",
        ),
        "effective_stale_date_from_last_modified": Column(
            "Effective stale date due to effective last modified date",
            "Take 'Effective Last Modified date' from timetable data catalogue "
            "plus 12 months.",
        ),
        "last_modified_lt_effective_stale_date_otc": Column(
            "Last modified date < Effective stale date due to " "OTC effective date",
            "If last modified date is less than "
            "Effective stale date due to OTC effective date "
            "Then TRUE "
            "Else FALSE.",
        ),
        "effective_stale_date_from_otc_effective": Column(
            "Effective stale date due to OTC effective date",
            "Effective date” (timetable data catalogue) minus 70 days.",
        ),
        "effective_seasonal_start": Column(
            "Effective Seasonal Start Date",
            "If Seasonal Start Date is present "
            "Then Seasonal Start Date minus 42 days "
            "Else null.",
        ),
        "seasonal_start": Column(
            "Seasonal Start Date",
            "If service has been assigned a date range from within the "
            "seasonal services flow "
            "Then take start date "
            "Else null.",
        ),
        "seasonal_end": Column(
            "Seasonal End Date",
            "If service has been assigned a date range from within the "
            "seasonal services flow "
            "Then take end date "
            "Else null.",
        ),
        "revision_number": Column(
            "Data set Revision Number",
            "The service revision number date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "string_lines": Column(
            "Data set Line Name",
            "The line name(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "origin": Column(
            "Origin",
            "The origin element as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "destination": Column(
            "Destination",
            "The destination element as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "otc_operator_id": Column(
            "Operator ID",
            "The operator ID element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "operator_name": Column(
            "Operator Name",
            "The operator name element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "address": Column(
            "Address",
            "The address as extracted from the database of the Office of "
            "the Traffic Commissioner (OTC)",
        ),
        "otc_licence_number": Column(
            "OTC Licence Number",
            "The licence number element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "licence_status": Column(
            "Licence Status",
            "The licence status element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "registration_number": Column(
            "OTC Registration Number",
            "The registration number element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "service_type_description": Column(
            "Service Type Description",
            "The service type description element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "variation_number": Column(
            "Variation Number",
            "The variation number element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "service_number": Column(
            "OTC Service Number",
            "The service number element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "start_point": Column(
            "Start Point",
            "The start point element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "finish_point": Column(
            "Finish Point",
            "The finish point element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "via": Column(
            "Via",
            "The via element as extracted from the database of the Office of "
            "the Traffic Commissioner (OTC)",
        ),
        "granted_date": Column(
            "Granted Date",
            "The granted date element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "expiry_date": Column(
            "Expiry Date",
            "The expiry date element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "effective_date": Column(
            "Effective Date",
            "The effective date element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "received_date": Column(
            "Received Date",
            "The received date element as extracted from the database of "
            "the Office of the Traffic Commissioner (OTC)",
        ),
        "service_type_other_details": Column(
            "Service Type Other Details",
            "The service type other details element as extracted from "
            "the database of the Office of the Traffic Commissioner (OTC)",
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


def add_staleness_metrics(df: pd.DataFrame, today: datetime.date) -> pd.DataFrame:
    today = np.datetime64(today)
    df["last_modified_date"] = df["modification_datetime"].dt.date
    df["effective_last_modified_date"] = df["last_modified_date"]

    df["effective_seasonal_start"] = df["seasonal_start"] - pd.Timedelta(days=42)

    df["effective_stale_date_from_end_date"] = df[
        "operating_period_end_date"
    ] - pd.Timedelta(days=42)
    defer_one_year = (
        lambda d: d if pd.isna(d) else datetime.date(d.year + 1, d.month, d.day)
    )
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

    """
    effective_stale_date_from_end_date = effective_date - 42 days
    effective_stale_date_from_last_modified = last_modified_date - 365 days (or 1 year)
    """
    staleness_12_months = (
        (
            pd.isna(df["effective_stale_date_from_end_date"])
            | (
                df["effective_stale_date_from_last_modified"]
                < df["effective_stale_date_from_end_date"]
            )
        )
        & (df["effective_stale_date_from_last_modified"] <= today)
        & (df["last_modified_date"] >= df["effective_date"])
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
    df["staleness_status"] = np.select(
        condlist=[staleness_42_day_look_ahead, staleness_12_months, staleness_otc],
        choicelist=[
            "Stale - 42 day look ahead",
            "Stale - 12 months old",
            "Stale - OTC Variation",
        ],
        default="Not Stale",
    )
    return df


def add_requires_attention_column(
    df: pd.DataFrame, today: datetime.date
) -> pd.DataFrame:
    requires_attention = (
        (df["scope_status"] == "In Scope")
        & (df["seasonal_status"] != "Out of Season")
        & (
            (df["staleness_status"] != "Not Stale")
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

    txc_df["bods_compliant"] = txc_df["bods_compliant"].map(cast_boolean_to_string)
    merged = pd.merge(otc_df, txc_df, on="service_code", how="outer")

    for field, type_ in castings:
        merged[field] = merged[field].astype(type_)

    merged.sort_values("dataset_id", inplace=True)
    merged["organisation_name"] = merged.apply(lambda x: add_operator_name(x), axis=1)
    merged = add_status_columns(merged)
    merged = add_seasonal_status(merged, today)
    merged = add_staleness_metrics(merged, today)
    merged = add_requires_attention_column(merged, today)
    merged["score"] = merged["score"].map(
        lambda value: f"{int(round_down(value) * 100)}%" if not pd.isna(value) else ""
    )
    rename_map = {
        old_name: column_tuple.field_name
        for old_name, column_tuple in TIMETABLE_COLUMN_MAP.items()
    }
    merged = merged[TIMETABLE_COLUMN_MAP.keys()].rename(columns=rename_map)
    return merged


def get_timetable_catalogue_csv():
    return _get_timetable_catalogue_dataframe().to_csv(index=False)
