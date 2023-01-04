import pandas as pd
from waffle import flag_is_active

from transit_odp.fares.models import FaresMetadata
from transit_odp.organisation.csv import EmptyDataFrame


def _get_fares_data_catalogue_dataframe() -> pd.DataFrame:
    fares_df = pd.DataFrame.from_records(
        FaresMetadata.objects.get_active_fares_files().values()
    )

    if fares_df.empty:
        raise EmptyDataFrame()

    fares_df.sort_values("revision_id", inplace=True)
    return fares_df


def get_fares_data_catalogue_csv():
    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
    if is_fares_validator_active:
        return _get_fares_data_catalogue_dataframe().to_csv(index=False)
