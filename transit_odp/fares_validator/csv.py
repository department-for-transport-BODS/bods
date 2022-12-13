from collections import OrderedDict
from typing import Optional

import numpy as np
import pandas as pd

from transit_odp.common.collections import Column
from transit_odp.common.utils import round_down
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.fares.models import FaresMetadata 

def _get_fares_data_catalogue_dataframe() -> pd.DataFrame:
    fares_df = pd.DataFrame.from_records(
        FaresMetadata.objects.get_active_fares_files().values()
    )
    
    print("fares_df", fares_df)
    
    if fares_df.empty:
        raise EmptyDataFrame()

    fares_df.sort_values("revision_id", inplace=True)
    return fares_df


def get_fares_data_catalogue_csv():
    return _get_fares_data_catalogue_dataframe().to_csv(index=False)
