import tempfile

import pandas as pd

from transit_odp.site_admin.csv.dailyconsumer import get_consumer_breakdown_df

AGGREGATES_COLUMN_MAP = {
    "date": "Date",
    "requestor_id": "Number of unique consumers",
    "total_requests": "Number of API requests",
    "total_download_timetables": (
        "Number of total timetables downloads (using download all)"
    ),
    "total_download_avl": (
        "Number of total location data downloads (using download all)"
    ),
    "total_download_fares": "Number of total fares data downloads (using download all)",
}


def get_daily_aggregates_df(start, end):
    consumer_breakdown = get_consumer_breakdown_df(start, end)
    if consumer_breakdown.empty:
        return pd.DataFrame(columns=AGGREGATES_COLUMN_MAP.values())

    consumer_breakdown.drop(columns="requestor__email", inplace=True)
    daily_aggregates = consumer_breakdown.groupby("date", as_index=False).agg(
        {
            "requestor_id": "nunique",
            "total_requests": "sum",
            "total_download_timetables": "sum",
            "total_download_avl": "sum",
            "total_download_fares": "sum",
        }
    )
    return daily_aggregates


def get_daily_aggregates_csv(start, end):
    csvfile = tempfile.NamedTemporaryFile(mode="w")
    df = get_daily_aggregates_df(start, end)
    df = df.rename(columns=AGGREGATES_COLUMN_MAP)
    df.to_csv(csvfile, index=False)
    csvfile.seek(0)
    return csvfile
