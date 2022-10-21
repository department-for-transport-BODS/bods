import tempfile

import pandas as pd

from transit_odp.site_admin.models import APIRequest, ResourceRequestCounter

CONSUMER_BREAKDOWN_COLUMN_MAP = {
    "date": "Date",
    "requestor_id": "Consumer ID",
    "requestor__email": "Email",
    "total_requests": "Number of daily API requests",
    "total_download_timetables": (
        "Number of timetables daily downloads (using Download all)"
    ),
    "total_download_avl": (
        "Number of location data daily downloads (using Download all)"
    ),
    "total_download_fares": "Number of fares daily downloads (using Download all)",
}
API_METRICS = ["total_requests"]
REQUEST_METRICS = [
    "total_download_timetables",
    "total_download_fares",
    "total_download_avl",
]


def get_api_queryset(start, end):
    return APIRequest.objects.get_requests_per_day_per_user().filter(
        created__range=(start, end)
    )


def get_resource_queryset(start, end):
    return ResourceRequestCounter.objects.get_requests_per_day_per_user().filter(
        date__gte=start.date(), date__lte=end.date()
    )


def get_consumer_breakdown_df(start, end):
    api_df = pd.DataFrame.from_records(get_api_queryset(start, end))
    request_df = pd.DataFrame.from_records(get_resource_queryset(start, end))
    if api_df.empty and request_df.empty:
        return pd.DataFrame(columns=CONSUMER_BREAKDOWN_COLUMN_MAP.values())

    elif api_df.empty:
        for metric in API_METRICS:
            request_df[metric] = 0
        consumer_breakdown = request_df

    elif request_df.empty:
        for metric in REQUEST_METRICS:
            api_df[metric] = 0
        api_df["date"] = api_df.apply(lambda row: row.day.date(), axis=1)
        consumer_breakdown = api_df

    else:
        api_df["date"] = api_df.apply(lambda row: row.day.date(), axis=1)
        consumer_breakdown = api_df.merge(
            request_df, how="outer", on=["date", "requestor_id", "requestor__email"]
        )
        # We need to sort the final df after merging
        consumer_breakdown = consumer_breakdown.sort_values(by=["date"])
        consumer_breakdown.fillna(0, inplace=True)
        # Not sure why but fields that are not joining fields are cast to float
        # this casts them back to integers
        for metric in API_METRICS + REQUEST_METRICS:
            consumer_breakdown[metric] = consumer_breakdown[metric].astype(int)

    consumer_breakdown = consumer_breakdown[CONSUMER_BREAKDOWN_COLUMN_MAP.keys()]

    return consumer_breakdown


def get_consumer_breakdown_csv(start, end):
    df = get_consumer_breakdown_df(start, end)
    df = df.rename(columns=CONSUMER_BREAKDOWN_COLUMN_MAP)
    csvfile = tempfile.NamedTemporaryFile(mode="w")
    df.to_csv(csvfile, index=False)
    csvfile.seek(0)
    return csvfile
