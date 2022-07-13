import pandas as pd

from transit_odp.organisation.csv.consumer_interactions import (
    get_api_list_map_df,
    get_bulk_downloads_map_df,
    get_datasets_df,
)
from transit_odp.site_admin.models import APIRequest, ResourceRequestCounter

DATASET_COLUMNS = [
    "requestor_id",
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


def get_api_requests_df() -> pd.DataFrame:
    qs = APIRequest.objects.get_user_path_info_requests_from_last_7_days().values(
        "path_info", "requestor_id", "total_requests"
    )
    return pd.DataFrame.from_records(qs)


def get_download_requests_df() -> pd.DataFrame:
    qs = ResourceRequestCounter.objects.get_requests_from_last_7_days().values(
        "path_info", "requestor_id", "counter"
    )
    return pd.DataFrame.from_records(qs)


def get_direct_api_hits_per_dataset_per_user(
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
            "requestor_id",
            "organisation_id",
            "dataset_type_pretty",
            "total_subscriptions",
            "total_requests",
        ]
    ].rename(columns={"total_requests": "api_direct_hits"})
    df = df.assign(api_list_hits=0, bulk_downloads=0, direct_downloads=0)
    return df


def get_direct_download_hits_per_dataset_per_user(
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
            "requestor_id",
            "organisation_id",
            "dataset_type_pretty",
            "total_subscriptions",
            "counter",
        ]
    ].rename(columns={"counter": "direct_downloads"})
    df = df.assign(api_list_hits=0, bulk_downloads=0, api_direct_hits=0)
    return df


def get_bulk_download_hits_per_dataset_per_user(
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
        ["requestor_id", "counter", "dataset_type_pretty"]
    ].rename(columns={"counter": "bulk_downloads"})

    df = bulk_downloads_per_day.merge(
        datasets[
            [
                "organisation_id",
                "dataset_type_pretty",
                "total_subscriptions",
            ]
        ],
        on="dataset_type_pretty",
    )
    df = df.assign(api_list_hits=0, direct_downloads=0, api_direct_hits=0)
    return df


def get_api_list_hits_per_dataset_per_user(
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
        ["requestor_id", "total_requests", "dataset_type_pretty"]
    ].rename(columns={"total_requests": "api_list_hits"})

    df = api_list_requests_per_day.merge(
        datasets[
            [
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
    all_downloads = get_download_requests_df()
    all_published_datasets = get_datasets_df()

    if all_published_datasets.empty:
        return pd.DataFrame(columns=COLUMNS)

    direct_api_hits_per_dataset_per_user = get_direct_api_hits_per_dataset_per_user(
        all_api_hits, all_published_datasets
    )

    direct_downloads_per_dataset_per_user = (
        get_direct_download_hits_per_dataset_per_user(
            all_downloads, all_published_datasets
        )
    )

    bulk_downloads_per_dataset_per_user = get_bulk_download_hits_per_dataset_per_user(
        all_downloads, all_published_datasets
    )

    api_list_hits_per_dataset_per_user = get_api_list_hits_per_dataset_per_user(
        all_api_hits, all_published_datasets
    )

    return pd.concat(
        [
            api_list_hits_per_dataset_per_user,
            direct_api_hits_per_dataset_per_user,
            bulk_downloads_per_dataset_per_user,
            direct_downloads_per_dataset_per_user,
        ]
    )


def get_all_consumer_interaction_stats() -> pd.DataFrame:
    df = get_all_consumer_interactions_df()

    df = df.groupby("organisation_id", as_index=False).agg(
        unique_users=pd.NamedAgg(column="requestor_id", aggfunc="nunique"),
        bulk_downloads_total=pd.NamedAgg(column="bulk_downloads", aggfunc="sum"),
        direct_downloads_total=pd.NamedAgg(column="direct_downloads", aggfunc="sum"),
        api_direct_hits_total=pd.NamedAgg(column="api_direct_hits", aggfunc="sum"),
        api_list_hits_total=pd.NamedAgg(column="api_list_hits", aggfunc="sum"),
    )
    if not len(df):
        return pd.DataFrame(columns=COLUMNS)

    return df
