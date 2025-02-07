import logging
from transit_odp.avl.constants import AVL_GRANULARITY_WEEKLY
from transit_odp.avl.models import PostPublishingCheckReport
from django.db.models import Subquery
from zipfile import ZipFile
import pandas as pd
from io import BytesIO
from django.core.cache import cache
import pickle


logger = logging.getLogger(__name__)

ALL_SIRIVM_FILENAME = "all_siri_vm_analysed.csv"
UNCOUNTED_VEHICLE_ACTIVITY_FILENAME = "uncountedvehicleactivities.csv"
OPERATOR_REF_FILENAME = "originref.csv"
DIRECTION_REF_FILENAME = "directionref.csv"
DESTINATION_REF_FILENAME = "destinationref.csv"
CACHE_KEY = "weekly_vehicle_activity_error_operatorref_linenames"


def get_vehicle_activity_operatorref_linename() -> pd.DataFrame:
    """Get the value for weekly operator ref and linename

    Returns:
        pd.DataFrame: Dataframe either from cache or from zip
    """
    value_in_cache = cache.get(CACHE_KEY, None)
    logger.info("Vehicle activites fetching from cache")
    if value_in_cache is None:
        logger.info("Vehicle activites not present in cache, setting new value")
        set_value_in_cache()
        value_in_cache = cache.get(CACHE_KEY, None)

    df = pickle.loads(value_in_cache)
    return df


def set_value_in_cache():
    errors_df = read_all_linenames_from_weekly_files()
    serialized_df = pickle.dumps(errors_df)
    cache.set(CACHE_KEY, serialized_df, timeout=(7 * 24 * 60 * 60))


def reset_vehicle_activity_in_cache() -> None:
    cache.delete(CACHE_KEY)
    set_value_in_cache()


def read_all_linenames_from_weekly_files() -> pd.DataFrame:
    """Get errors dataframe and all sirivm analysed dataframe
    From the weekly PPC report zip files

    Returns:
        pd.DataFrame: dataframe containing lines and operator ref
    """
    try:
        latest_zip_files = get_latest_reports_from_db()
        logger.info(f"Total {len(latest_zip_files)} Found with vehicle activities.")
        errors_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
        for record in latest_zip_files:
            with record.file.open("rb") as zip_file_obj:
                zip_data = BytesIO(zip_file_obj.read())
                with ZipFile(zip_data, "r") as z:
                    try:
                        with z.open(ALL_SIRIVM_FILENAME) as af:
                            all_activity_df = pd.read_csv(
                                af,
                                dtype={
                                    "VehicleRef": "object",
                                    "DatedVehicleJourneyRef": "object",
                                    "LineRef": "object",
                                },
                            )
                    except Exception as e:
                        logger.error(f"Exception: File {ALL_SIRIVM_FILENAME} not found")
                        logger.error(str(e))
                        all_activity_df = pd.DataFrame(
                            columns=[
                                "DatedVehicleJourneyRef",
                                "VehicleRef",
                                "DestinationRef",
                            ]
                        )

                    try:
                        with z.open(UNCOUNTED_VEHICLE_ACTIVITY_FILENAME) as uf:
                            df = pd.read_csv(uf, dtype={"LineRef": "object"})
                            df = df[["OperatorRef", "LineRef"]]
                            errors_df = pd.concat([df, errors_df])
                    except Exception as e:
                        logger.error(
                            f"Exception: File {UNCOUNTED_VEHICLE_ACTIVITY_FILENAME} not found"
                        )
                        logger.error(str(e))

                    errors_df = pd.concat(
                        [
                            errors_df,
                            get_destinationref_df(z, all_activity_df),
                            get_originref_df(z, all_activity_df),
                            get_directionref_df(z, all_activity_df),
                        ]
                    )
                    errors_df.drop_duplicates(inplace=True)
                    errors_df.reset_index(inplace=True, drop=True)
        logger.info(f"Found {len(errors_df)} lines in error in weekly ppc report.")
        return errors_df
    except Exception as e:
        logger.error("Exception: For getting vehicle activity and operator refs.")
        logger.error(str(e))
        return pd.DataFrame(columns=["OperatorRef", "LineRef"])


def get_latest_reports_from_db():
    """Get the list of all the zip files generated from the
    Weekly PPC report

    Returns:
        Queryset with list of zipfile record
    """
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


def get_originref_df(zipfile: ZipFile, all_activity_df: pd.DataFrame) -> pd.DataFrame:
    """Get line ref and operator ref from origin ref csv from
    PPC weekly zip file

    Following columns will be used for comparision in origin ref
    and all sirivm analysed
    DatedVehicleJourneyRef, VehicleRef, OriginRef

    Args:
        zipfile (ZipFile): zip file object to read the origin ref df
        all_activity_df (pd.DataFrame): all sirivm analysed df

    Returns:
        pd.DataFrame: dataframe with lineref and operator ref
    """
    try:
        with zipfile.open(OPERATOR_REF_FILENAME) as uf:
            origin_ref_df = pd.read_csv(
                uf,
                dtype={
                    "VehicleRef in SIRI": "object",
                    "DatedVehicleJourneyRef in SIRI": "object",
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
            filtered_df.reset_index(inplace=True, drop=True)

            return filtered_df
    except Exception as e:
        logger.error(
            f"Exception: In Reading OperatorRef file in zip {zipfile.filename}."
        )
        logger.error(str(e))
        return pd.DataFrame(columns=["OperatorRef", "LineRef"])


def get_directionref_df(
    zipfile: ZipFile, all_activity_df: pd.DataFrame
) -> pd.DataFrame:
    """Get line ref and operator ref from direction ref csv from
    PPC weekly zip file

    Following columns will be used for comparision in direction ref
    and all sirivm analysed
    DatedVehicleJourneyRef, VehicleRef, DirectionRef

    Args:
        zipfile (ZipFile): zip file object to read the direction ref df
        all_activity_df (pd.DataFrame): all sirivm analysed df

    Returns:
        pd.DataFrame: dataframe with lineref and operator ref
    """
    try:
        with zipfile.open(DIRECTION_REF_FILENAME) as uf:
            origin_ref_df = pd.read_csv(
                uf,
                dtype={
                    "VehicleRef in SIRI": "object",
                    "DatedVehicleJourneyRef in SIRI": "object",
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
            filtered_df.reset_index(inplace=True, drop=True)

            return filtered_df
    except Exception as e:
        logger.error(
            f"Exception: In Reading DirectionRef file in zip {zipfile.filename}."
        )
        logger.error(str(e))
        return pd.DataFrame(columns=["OperatorRef", "LineRef"])


def get_destinationref_df(
    zipfile: ZipFile, all_activity_df: pd.DataFrame
) -> pd.DataFrame:
    """Get line ref and operator ref from desination ref csv from
    PPC weekly zip file

    Following columns will be used for comparision in destination ref
    and all sirivm analysed
    DatedVehicleJourneyRef, VehicleRef, DestinationRef

    Args:
        zipfile (ZipFile): zip file object to read the destination ref df
        all_activity_df (pd.DataFrame): all sirivm analysed df

    Returns:
        pd.DataFrame: dataframe with lineref and operator ref
    """
    try:
        with zipfile.open(DESTINATION_REF_FILENAME) as uf:
            origin_ref_df = pd.read_csv(
                uf,
                dtype={
                    "VehicleRef in SIRI": "object",
                    "DatedVehicleJourneyRef in SIRI": "object",
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
            filtered_df.reset_index(inplace=True, drop=True)

            return filtered_df
    except Exception as e:
        logger.error(
            f"Exception: In Reading DestinationRef file in zip {zipfile.filename}."
        )
        logger.error(str(e))
        return pd.DataFrame(columns=["OperatorRef", "LineRef"])
