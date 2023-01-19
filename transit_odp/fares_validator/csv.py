from collections import OrderedDict

import pandas as pd

from transit_odp.common.collections import Column
from transit_odp.fares.models import DataCatalogueMetaData
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.models.organisations import OperatorCode

METADATA_COLUMNS = (
    "fares_metadata_id",
    "xml_file_name",
    "valid_from",
    "valid_to",
    "national_operator_code",
    "line_id",
    "line_name",
    "atco_area",
    "tariff_basis",
    "product_type",
    "product_name",
    "user_type",
    "last_updated_date",
    "operator_id",
    "organisation_name",
    "is_fares_compliant",
)

FARES_DATA_COLUMN_MAP = OrderedDict(
    {
        "fares_metadata_id": Column(
            "Dataset ID",
            "",
        ),
        "xml_file_name": Column(
            "XML file name",
            "",
        ),
        "organisation_name": Column(
            "Organisation Name",
            "",
        ),
        "national_operator_code": Column(
            "National Operator Code",
            "",
        ),
        "operator_id": Column(
            "Operator ID",
            "",
        ),
        "is_fares_compliant": Column(
            "BODS Compliant",
            "",
        ),
        "last_updated_date": Column(
            "Last updated date",
            "",
        ),
        "valid_from": Column(
            "Valid from",
            "",
        ),
        "valid_to": Column(
            "Valid to",
            "",
        ),
        "line_id": Column(
            "Line ids",
            "",
        ),
        "line_name": Column(
            "Line Name",
            "",
        ),
        "atco_area": Column(
            "ATCO Area",
            "",
        ),
        "tariff_basis": Column(
            "TariffBasis",
            "",
        ),
        "product_type": Column(
            "ProductType",
            "",
        ),
        "product_name": Column(
            "ProductName",
            "",
        ),
        "multioperator": Column(
            "Multioperator",
            "",
        ),
    }
)


def _get_fares_data_catalogue_dataframe() -> pd.DataFrame:
    fares_df = pd.DataFrame.from_records(
        DataCatalogueMetaData.objects.get_active_fares_files().values(*METADATA_COLUMNS)
    )
    nocs = fares_df["national_operator_code"].tolist()
    nocs_df = pd.DataFrame.from_records(OperatorCode.objects.get_nocs().values())
    multioperator_list = add_multioperator_status(nocs, nocs_df)
    multioperator_df = pd.DataFrame(multioperator_list, columns=["multioperator"])

    if fares_df.empty or multioperator_df.empty:
        raise EmptyDataFrame()

    merged = pd.merge(fares_df, multioperator_df, on=fares_df.index, how="outer")
    rename_map = {
        old_name: column_tuple.field_name
        for old_name, column_tuple in FARES_DATA_COLUMN_MAP.items()
    }
    merged = merged[FARES_DATA_COLUMN_MAP.keys()].rename(columns=rename_map)

    merged.sort_values("Dataset ID", inplace=True)
    return merged


def get_fares_data_catalogue_csv():
    return _get_fares_data_catalogue_dataframe().to_csv(index=False)


def add_multioperator_status(nocs, nocs_df) -> list:
    """
    Calculates if the NOCs belong to the same organisation or not
    If all NOCs doesn't belong to same organisation then Multioperator is True
    """
    multioperator_list = []
    for operator_codes in nocs:
        orgs = []
        for operator in operator_codes:
            org = nocs_df.loc[nocs_df["noc"] == operator, "organisation_id"].iloc[0]
            if org:
                orgs.append(org)
        if len(set(orgs)) == 1:
            multioperator_list.append("No")
        elif len(set(orgs)) > 1:
            multioperator_list.append("Yes")
    if multioperator_list:
        return multioperator_list
