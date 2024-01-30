import pandas as pd
from django.db.models import Count

from config.hosts import DATA_HOST
from transit_odp.common.utils import reverse_path
from transit_odp.organisation.models import Dataset
from transit_odp.site_admin.models import APIRequest, ResourceRequestCounter

CSV_HEADERS = [
    "Date",
    "Dataset ID",
    "DataType",
    "Number of Current Subscriptions",
    "Number of downloads (dataset download)",
    "Number of downloads (download all)",
    "Number of API requests",
]

API_LIST_URLS = [
    reverse_path("api:feed-list", host=DATA_HOST),
    reverse_path("api:avldatafeedapi", host=DATA_HOST),
    reverse_path("api:gtfsrtdatafeedapi", host=DATA_HOST),
    reverse_path("api:fares-api-list", host=DATA_HOST),
]

BULK_DOWNLOAD_URLS = [
    reverse_path("downloads-bulk", host=DATA_HOST),
    reverse_path("gtfs-file-download", kwargs={"id": "all"}, host=DATA_HOST),
    reverse_path("downloads-avl-bulk", host=DATA_HOST),
    reverse_path("download-gtfsrt-bulk", host=DATA_HOST),  # avl
    reverse_path("downloads-fares-bulk", host=DATA_HOST),
]

DATASET_COLUMNS = [
    "date",
    "dataset_id",
    "organisation_id",
    "dataset_type_pretty",
    "total_subscriptions",
]

COLUMNS = [
    *DATASET_COLUMNS,
    "direct_downloads",
    "bulk_downloads",
    "api_direct_hits",
    "api_list_hits",
]


def _get_total_api_hits(row: pd.Series) -> int:
    return row["api_direct_hits"] + row["api_list_hits"]


def get_bulk_downloads_map_df() -> pd.DataFrame:
    """
    Maps the bulk download urls to the dataset types
    """
    return pd.DataFrame(
        {
            "path_info": BULK_DOWNLOAD_URLS,
            "dataset_type_pretty": [
                "Timetables",
                "Timetables",
                "Automatic Vehicle Locations",
                "Automatic Vehicle Locations",
                "Fares",
            ],
        }
    )


def get_api_list_map_df() -> pd.DataFrame:
    """
    Maps the api list urls to the dataset types
    """
    return pd.DataFrame(
        {
            "path_info": API_LIST_URLS,
            "dataset_type_pretty": [
                "Timetables",
                "Automatic Vehicle Locations",
                "Automatic Vehicle Locations",
                "Fares",
            ],
        }
    )


def get_api_requests_df() -> pd.DataFrame:
    qs = (
        APIRequest.objects.get_requests_from_last_30_days()
        .exclude_query_string()
        .add_day_from_created(as_date=True)
        .values("day", "path_info")
        .annotate(total_requests=Count("id"))
    )
    df = pd.DataFrame.from_records(qs)
    df.rename(columns={"day": "date"}, inplace=True)
    return df


def get_download_request_df() -> pd.DataFrame:
    # fmt: off
    qs = (
        ResourceRequestCounter
        .objects
        .get_requests_from_last_30_days()
        .get_requests_per_day()
    )
    # fmt: on
    df = pd.DataFrame.from_records(qs)
    return df


def get_datasets_df() -> pd.DataFrame:
    qs = (
        Dataset.objects.get_published()
        .add_dataset_download_url()
        .add_api_url()
        .add_total_subscriptions()
        .add_pretty_dataset_type()
        .values(
            "id",
            "organisation_id",
            "dataset_type_pretty",
            "total_subscriptions",
            "api_detail_url",
            "dataset_download_url",
        )
    )

    df = pd.DataFrame.from_records(qs)
    df.rename(columns={"id": "dataset_id"}, inplace=True)
    return df


def get_direct_api_hits_per_dataset_per_day(
    api_hits: pd.DataFrame, datasets: pd.DataFrame
) -> pd.DataFrame:
    """
    joins dataset information onto api detail views
    """

    if api_hits.empty:
        return pd.DataFrame(columns=COLUMNS)

    df = api_hits.merge(
        datasets,
        left_on="path_info",
        right_on="api_detail_url",
        suffixes=["", "_from_api"],
    )

    df = df[
        [
            "date",
            "dataset_id",
            "organisation_id",
            "dataset_type_pretty",
            "total_subscriptions",
            "total_requests",
        ]
    ].rename(columns={"total_requests": "api_direct_hits"})
    df = df.assign(api_list_hits=0, bulk_downloads=0, direct_downloads=0)
    return df


def get_direct_download_hits_per_dataset_per_day(
    downloads: pd.DataFrame, datasets: pd.DataFrame
) -> pd.DataFrame:
    """
    joins dataset information onto the download views
    """
    if downloads.empty:
        return pd.DataFrame(columns=COLUMNS)

    df = downloads.merge(
        datasets,
        left_on="path_info",
        right_on="dataset_download_url",
        suffixes=["", "_from_downloads"],
    )
    df = df[
        [
            "date",
            "dataset_id",
            "organisation_id",
            "dataset_type_pretty",
            "total_subscriptions",
            "total_requests",
        ]
    ].rename(columns={"total_requests": "direct_downloads"})
    df = df.assign(api_list_hits=0, bulk_downloads=0, api_direct_hits=0)
    return df


def get_bulk_download_hits_per_dataset_per_day(
    downloads: pd.DataFrame, datasets: pd.DataFrame
) -> pd.DataFrame:
    """
    first joins dataset type information onto the bulk download list views then
    joins onto the dateset so we can tell which datasets a list view refers too.
    """

    if downloads.empty:
        return pd.DataFrame(columns=COLUMNS)

    bulk_downloads_per_day = downloads.merge(
        get_bulk_downloads_map_df(), on="path_info"
    )
    bulk_downloads_per_day = bulk_downloads_per_day[
        ["date", "total_requests", "dataset_type_pretty"]
    ].rename(columns={"total_requests": "bulk_downloads"})

    df = bulk_downloads_per_day.merge(
        datasets[
            [
                "dataset_id",
                "organisation_id",
                "dataset_type_pretty",
                "total_subscriptions",
            ]
        ],
        on="dataset_type_pretty",
    )
    df = df.assign(api_list_hits=0, direct_downloads=0, api_direct_hits=0)
    return df


def get_api_list_hits_per_dataset_per_day(
    api_hits: pd.DataFrame, datasets: pd.DataFrame
) -> pd.DataFrame:
    """
    first joins dataset type information onto the api list views then
    joins onto the dateset so we can tell which datasets a list view refers too.
    """
    if api_hits.empty:
        return pd.DataFrame(columns=COLUMNS)

    api_list_requests_per_day = api_hits.merge(get_api_list_map_df(), on="path_info")

    api_list_requests_per_day = api_list_requests_per_day[
        ["date", "total_requests", "dataset_type_pretty"]
    ].rename(columns={"total_requests": "api_list_hits"})

    df = api_list_requests_per_day.merge(
        datasets[
            [
                "dataset_id",
                "organisation_id",
                "dataset_type_pretty",
                "total_subscriptions",
            ]
        ],
        on="dataset_type_pretty",
    )
    df = df.assign(bulk_downloads=0, direct_downloads=0, api_direct_hits=0)
    return df


def get_all_consumer_interactions_df() -> pd.DataFrame:
    all_api_hits = get_api_requests_df()
    all_downloads = get_download_request_df()
    all_published_datasets = get_datasets_df()

    if all_published_datasets.empty:
        return pd.DataFrame(columns=COLUMNS)

    direct_api_hits_per_dataset_per_day = get_direct_api_hits_per_dataset_per_day(
        all_api_hits, all_published_datasets
    )

    direct_downloads_per_dataset_per_day = get_direct_download_hits_per_dataset_per_day(
        all_downloads, all_published_datasets
    )

    bulk_downloads_per_dataset_per_day = get_bulk_download_hits_per_dataset_per_day(
        all_downloads, all_published_datasets
    )

    api_list_hits_per_dataset_per_day = get_api_list_hits_per_dataset_per_day(
        all_api_hits, all_published_datasets
    )

    return pd.concat(
        [
            api_list_hits_per_dataset_per_day,
            direct_api_hits_per_dataset_per_day,
            bulk_downloads_per_dataset_per_day,
            direct_downloads_per_dataset_per_day,
        ]
    )


def get_all_monthly_breakdown_stats() -> pd.DataFrame:
    df = get_all_consumer_interactions_df()

    df = df.groupby(
        [
            "date",
            "dataset_id",
            "organisation_id",
            "dataset_type_pretty",
            "total_subscriptions",
        ],
        as_index=False,
    ).sum()

    columns = COLUMNS[:-2] + ["total_api_hits"]
    if not len(df):
        return pd.DataFrame(columns=columns)

    df["total_api_hits"] = df.apply(lambda n: _get_total_api_hits(n), axis=1)
    df = df[columns]
    return df


def filter_interactions_to_organisation(
    interactions: pd.DataFrame, organisation_id: int
) -> pd.DataFrame:
    filtered = interactions[interactions["organisation_id"] == organisation_id]
    return filtered.drop(columns=["organisation_id"])
