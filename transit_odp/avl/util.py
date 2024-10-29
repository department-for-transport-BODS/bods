from transit_odp.avl.constants import AVL_GRANULARITY_WEEKLY
from transit_odp.avl.models import PostPublishingCheckReport
from django.db.models import Subquery
from zipfile import ZipFile
import pandas as pd

ALL_SIRIVM_FILENAME = "all_siri_vm_analysed.csv"
UNCOUNTED_VEHICLE_ACTIVITY_FILENAME = "uncountedvehicleactivities.csv"
OPERATOR_REF_FILENAME = "originref.csv"
DIRECTION_REF_FILENAME = "directionref.csv"
DESTINATION_REF_FILENAME = "destinationref.csv"


def get_vehicle_activity_operatorref_linename() -> tuple:
    errors_df, all_activity_df = read_all_avl_zip_files()

    return transform_avl_activity_operatorref_linename(
        errors_df
    ), transform_avl_activity_operatorref_linename(all_activity_df)


def read_all_avl_zip_files() -> tuple:
    latest_zip_files = get_latest_reports_from_db()
    errors_df = pd.DataFrame()
    all_activity_df_all = pd.DataFrame()
    for record in latest_zip_files:
        with ZipFile(record.file.path, "r") as z:
            with z.open(ALL_SIRIVM_FILENAME) as af:
                all_activity_df = pd.read_csv(
                    af,
                    dtype={"VehicleRef": "object", "DatedVehicleJourneyRef": "int64"},
                )

            with z.open(UNCOUNTED_VEHICLE_ACTIVITY_FILENAME) as uf:
                df = pd.read_csv(uf)
                df = df[["OperatorRef", "LineRef"]]
                errors_df = pd.concat([df, errors_df])

            errors_df = pd.concat(
                [
                    errors_df,
                    get_destinationref_df(z, all_activity_df),
                    get_originref_df(z, all_activity_df),
                    get_directionref_df(z, all_activity_df),
                ]
            )
            errors_df.drop_duplicates(inplace=True)
            all_activity_df_all = pd.concat([all_activity_df_all, all_activity_df])

    return errors_df, all_activity_df_all


def get_latest_reports_from_db():
    return (
        PostPublishingCheckReport.objects.filter(
            granularity=AVL_GRANULARITY_WEEKLY, vehicle_activities_analysed__gt=0
        )
        .filter(
            created=Subquery(
                PostPublishingCheckReport.objects.filter(
                    granularity=AVL_GRANULARITY_WEEKLY,
                    vehicle_activities_analysed__gt=0,  # line must be removed, not required in any of the env
                )
                .order_by("-created")
                .values("created")[:1]
            )
        )
        .all()
    )


def transform_avl_activity_operatorref_linename(csv_df: pd.DataFrame) -> pd.DataFrame:
    csv_df.drop_duplicates(inplace=True)
    return csv_df[["OperatorRef", "LineRef"]]


def get_originref_df(zipfile: ZipFile, all_activity_df: pd.DataFrame) -> pd.DataFrame:
    with zipfile.open(OPERATOR_REF_FILENAME) as uf:
        origin_ref_df = pd.read_csv(
            uf,
            dtype={
                "VehicleRef in SIRI": "object",
                "DatedVehicleJourneyRef in SIRI": "int64",
            },
        )
        origin_ref_df = origin_ref_df[
            [
                "DatedVehicleJourneyRef in SIRI",
                "VehicleRef in SIRI",
                "OriginRef in SIRI",
            ]
        ].rename(
            columns={
                "DatedVehicleJourneyRef in SIRI": "DatedVehicleJourneyRef",
                "VehicleRef in SIRI": "VehicleRef",
                "OriginRef in SIRI": "OriginRef",
            }
        )

        filtered_df = pd.merge(
            all_activity_df,
            origin_ref_df,
            on=["DatedVehicleJourneyRef", "VehicleRef", "OriginRef"],
            how="inner",
        )
        filtered_df = filtered_df[["OperatorRef", "LineRef"]]
        filtered_df.drop_duplicates(inplace=True)

        return filtered_df


def get_directionref_df(
    zipfile: ZipFile, all_activity_df: pd.DataFrame
) -> pd.DataFrame:
    with zipfile.open(DIRECTION_REF_FILENAME) as uf:
        origin_ref_df = pd.read_csv(
            uf,
            dtype={
                "VehicleRef in SIRI": "object",
                "DatedVehicleJourneyRef in SIRI": "int64",
            },
        )
        origin_ref_df = origin_ref_df[
            [
                "DatedVehicleJourneyRef in SIRI",
                "VehicleRef in SIRI",
                "DirectionRef in SIRI",
            ]
        ].rename(
            columns={
                "DatedVehicleJourneyRef in SIRI": "DatedVehicleJourneyRef",
                "VehicleRef in SIRI": "VehicleRef",
                "DirectionRef in SIRI": "DirectionRef",
            }
        )

        filtered_df = pd.merge(
            all_activity_df,
            origin_ref_df,
            on=["DatedVehicleJourneyRef", "VehicleRef", "DirectionRef"],
            how="inner",
        )
        filtered_df = filtered_df[["OperatorRef", "LineRef"]]
        filtered_df.drop_duplicates(inplace=True)

        return filtered_df


def get_destinationref_df(
    zipfile: ZipFile, all_activity_df: pd.DataFrame
) -> pd.DataFrame:
    with zipfile.open(DESTINATION_REF_FILENAME) as uf:
        origin_ref_df = pd.read_csv(
            uf,
            dtype={
                "VehicleRef in SIRI": "object",
                "DatedVehicleJourneyRef in SIRI": "int64",
            },
        )
        origin_ref_df = origin_ref_df[
            [
                "DatedVehicleJourneyRef in SIRI",
                "VehicleRef in SIRI",
                "DestinationRef in SIRI",
            ]
        ].rename(
            columns={
                "DatedVehicleJourneyRef in SIRI": "DatedVehicleJourneyRef",
                "VehicleRef in SIRI": "VehicleRef",
                "DestinationRef in SIRI": "DestinationRef",
            }
        )

        filtered_df = pd.merge(
            all_activity_df,
            origin_ref_df,
            on=["DatedVehicleJourneyRef", "VehicleRef", "DestinationRef"],
            how="inner",
        )
        filtered_df = filtered_df[["OperatorRef", "LineRef"]]
        filtered_df.drop_duplicates(inplace=True)

        return filtered_df
