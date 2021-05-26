import datetime
from typing import List

import pandas as pd

from transit_odp.pipelines.pipelines.dataset_etl.utils.models import ExtractedData


def concat_and_dedupe(dfs):
    data = pd.concat(dfs)
    data = data[~data.index.duplicated(keep="first")]
    return data


def aggregate_schema_version(extracts: List[ExtractedData]) -> str:
    s = set((extract.schema_version for extract in extracts))
    return ",".join(str for str in s)


def aggregate_line_count(extracts: List[ExtractedData]) -> int:
    return sum([extract.line_count for extract in extracts])


def aggregate_line_names(extracts: List[ExtractedData]) -> List[str]:
    # We want the line names unique and ordered
    line_names = [name for extract in extracts for name in extract.line_names]
    line_names = set(line_names)
    return sorted(line_names)


def aggregate_import_datetime(extracts: List[ExtractedData]) -> datetime:
    if extracts:
        return extracts[0].import_datetime
    else:
        return None
