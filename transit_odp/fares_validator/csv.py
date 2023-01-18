import pandas as pd
from django.db.models import Q

from transit_odp.fares.models import DataCatalogueMetaData
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.models.organisations import OperatorCode


def _get_fares_data_catalogue_dataframe() -> pd.DataFrame:
    fares_df = pd.DataFrame.from_records(
        DataCatalogueMetaData.objects.get_active_fares_files().values()
    )
    nocs = fares_df["national_operator_code"].tolist()
    multioperator_list = add_multioperator_status(nocs)
    multioperator_df = pd.DataFrame({"multioperator": multioperator_list})
    merged = pd.merge(fares_df, multioperator_df, on=fares_df.index, how="outer")

    if merged.empty:
        raise EmptyDataFrame()

    merged.sort_values("fares_metadata_id", inplace=True)
    return merged


def get_fares_data_catalogue_csv():
    return _get_fares_data_catalogue_dataframe().to_csv(index=False)


def add_multioperator_status(nocs):
    """
    Calculates if the NOCs belong to the same organisation or not
    If all NOCs doesn't belong to same organisation then Multioperator is True
    """
    multioperator_list = []
    for operator_codes in nocs:
        orgs = []
        for operator in operator_codes:
            org = OperatorCode.objects.filter(Q(noc=operator))
            if org:
                orgs.append(org.values_list("organisation_id")[0][0])
        if len(set(orgs)) == 1:
            multioperator_list.append("No")
        elif len(set(orgs)) > 1:
            multioperator_list.append("Yes")
    return multioperator_list
