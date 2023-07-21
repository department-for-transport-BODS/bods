from collections import OrderedDict

from django_hosts import reverse
from pandas import DataFrame, Series

from config.hosts import PUBLISH_HOST
from transit_odp.avl.proxies import AVLDataset
from transit_odp.common.collections import Column
from transit_odp.organisation.csv import EmptyDataFrame

AVL_COLUMN_MAP = OrderedDict(
    {
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS.",
        ),
        "id": Column(
            "Datafeed ID",
            (
                "The internal BODS generated ID of the operator/publisher "
                "providing data on BODS."
            ),
        ),
        "avl_to_timtables_matching_score": Column(
            "% AVL to Timetables feed matching score",
            (
                "This will be the latest score for the AVL "
                "feed this row belongs to (Data ID)."
            ),
        ),
        "matching_report_url": Column(
            "Latest matching report URL",
            (
                "This will be the same report url as the AVL data "
                "feed page report url from the dataset review page."
            ),
        ),
    }
)

AVL_FIELDS = (
    "organisation_name",
    "name",
    "organisation_id",
    "id",
    "avl_to_timtables_matching_score",
)


def get_matching_report_url(row: Series) -> str:
    if row["avl_to_timtables_matching_score"] is not None:
        return reverse(
            "avl:download-matching-report",
            kwargs={"pk": row["id"], "pk1": row["organisation_id"]},
            host=PUBLISH_HOST,
        )
    return ""


def _get_avl_data_catalogue() -> DataFrame:
    avl_df = DataFrame.from_records(
        AVLDataset.objects.get_location_data_catalogue().values(*AVL_FIELDS)
    )

    if avl_df.empty:
        raise EmptyDataFrame()

    avl_df["matching_report_url"] = avl_df.apply(
        lambda x: get_matching_report_url(x), axis=1
    )
    rename_mapping = {key: column.field_name for key, column in AVL_COLUMN_MAP.items()}
    avl_df = avl_df[AVL_COLUMN_MAP.keys()].rename(columns=rename_mapping)
    return avl_df


def get_avl_data_catalogue_csv() -> str:
    return _get_avl_data_catalogue().to_csv(index=False)
