from collections import OrderedDict

from django_hosts import reverse
from pandas import DataFrame, Series

from config.hosts import PUBLISH_HOST
from transit_odp.avl.constants import (
    AWAITING_REVIEW,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
)
from transit_odp.avl.proxies import AVLDataset
from transit_odp.common.collections import Column
from transit_odp.organisation.csv import EmptyDataFrame

AVL_COLUMN_MAP = OrderedDict(
    {
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS",
        ),
        "id": Column(
            "Datafeed ID",
            (
                "The internal BODS generated ID of the operator/publisher "
                "providing data on BODS"
            ),
        ),
        "avl_compliance": Column(
            "Feed Compliance Status",
            (
                "The compliance status of data feed on BODS as a result of the "
                "SIRI-VM validation checks done on BODS to check for the mandatory "
                "SIRI-VM profile elements"
            ),
        ),
        "report_url": Column(
            "Compliance Report URL",
            (
                "The link to the exact report generated as a result of the "
                "SIRI-VM validation check done on BODS. The results of the "
                "validation check can be viewed here"
            ),
        ),
    }
)

AVL_FIELDS = (
    "organisation_name",
    "name",
    "avl_compliance",
    "organisation_id",
    "id",
)


def get_validation_report_url(row: Series) -> str:
    if row["avl_compliance"] in (
        NON_COMPLIANT,
        PARTIALLY_COMPLIANT,
        AWAITING_REVIEW,
    ):
        return reverse(
            "avl:validation-report-download",
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

    avl_df["report_url"] = avl_df.apply(lambda x: get_validation_report_url(x), axis=1)
    rename_mapping = {key: column.field_name for key, column in AVL_COLUMN_MAP.items()}
    avl_df = avl_df[AVL_COLUMN_MAP.keys()].rename(columns=rename_mapping)
    return avl_df


def get_avl_data_catalogue_csv() -> str:
    return _get_avl_data_catalogue().to_csv(index=False)
