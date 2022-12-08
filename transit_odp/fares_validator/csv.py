from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd

from transit_odp.common.collections import Column
from transit_odp.common.utils import round_down
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.fares.models import FaresMetadata 
from transit_odp.organisation.models.data import ServiceCodeExemption, TXCFileAttributes
from transit_odp.otc.models import Service as OTCService

FARES_COLUMNS = (
    "num_of_fare_zones",
    "num_of_lines",
    "num_of_sales_offer_packages",
    "num_of_fare_products",
    "num_of_user_profiles",
    "valid_from",
    "valid_to",
    "stops",
)


FARES_COLUMN_MAP = OrderedDict(
    {
        "statuses": Column(
            "Service Statuses",
            "The publication status of the publisher’s data set on BODS. "
            "'Registered/Unregistered' refers to their status of registration "
            "with the OTC. 'Published/Unpublished' refers to if they have been "
            "published on BODS. 'Missing data' refers to OTC data we haven't been "
            "able to match to a BODS data set. 'Unassigned licence' refers to a data "
            "set that we haven't been able to find the OTC. 'Out of scope' refers to "
            "data deemed exempt from being reported on BODS by the DVSA/DfT Admin",
        ),
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS",
        ),
        "dataset_id": Column(
            "Dataset ID",
            "The internal BODS generated ID of the operator/publisher providing "
            "data on BODS",
        ),
        "score": Column(
            "DQ Score",
            "The DQ score assigned to the publisher’s data set as a result of "
            "the additional data quality checks done on timetables data on BODS",
        ),
        "bods_compliant": Column(
            "BODS Compliant",
            "The validation status and format of timetables data ",
        ),
        "last_updated_date": Column(
            "Last Updated Date",
            "The date that the data set/feed was last updated on BODS",
        ),
        "filename": Column(
            "XML Filename",
            "The exact name of the file provided to BODS. This is usually generated"
            " by the publisher or their supplier",
        ),
        "licence_number": Column(
            "Licence Number",
            "The License number(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "national_operator_code": Column(
            "National Operator Code",
            "The National Operator Code(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "service_code": Column(
            "Service Code",
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
            "The operating period end date as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "revision_number": Column(
            "Service Revision Number",
            "The service revision number date as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "string_lines": Column(
            "Line Name",
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
            "Registration Number",
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
            "Service Number",
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

def _get_fares_data_catalogue_dataframe() -> pd.DataFrame:
    print("Data>>>", FaresMetadata.objects.all().values())
    fares_df = pd.DataFrame.from_records(
        FaresMetadata.objects.all().values()
    )
    
    print("txc_df", fares_df)
    
    if fares_df.empty:
        raise EmptyDataFrame()

    castings = (
        ("dataset_id", "Int64"),
        ("revision_number", "Int64"),
        ("public_use", "boolean"),
        ("variation_number", "Int64"),
        ("otc_operator_id", "Int64"),
    )

    # fares_df["bods_compliant"] = fares_df["bods_compliant"].map(cast_boolean_to_string)
    # merged = pd.merge(fares_df, on="service_code", how="outer")

    # for field, type_ in castings:
    #     merged[field] = merged[field].astype(type_)

    fares_df.sort_values("revision_id", inplace=True)
    # merged = add_status_column(merged)
    # merged["score"] = merged["score"].map(
    #     lambda value: f"{int(round_down(value) * 100)}%" if not pd.isna(value) else ""
    # )
    # rename_map = {
    #     old_name: column_tuple.field_name
    #     for old_name, column_tuple in TIMETABLE_COLUMN_MAP.items()
    # }
    # merged = merged[TIMETABLE_COLUMN_MAP.keys()].rename(columns=rename_map)
    return fares_df


def get_fares_data_catalogue_csv():
    return _get_fares_data_catalogue_dataframe().to_csv(index=False)
