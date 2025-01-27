""" dataframes.py
A collection of utility functions for converting pandas dataframes to and from
BODS transxchange models.
"""

import logging
from collections import OrderedDict
from datetime import datetime
from typing import Iterator, List, Dict

import geopandas
import pandas as pd
from django.db.models.query import QuerySet
from shapely.geometry import Point

from transit_odp.organisation.models import DatasetRevision
from transit_odp.organisation.models.data import TXCFileAttributes
from transit_odp.transmodel.models import (
    BankHolidays,
    BookingArrangements,
    FlexibleServiceOperationPeriod,
    NonOperatingDatesExceptions,
    OperatingDatesExceptions,
    OperatingProfile,
    Service,
    ServicedOrganisations,
    ServicedOrganisationVehicleJourney,
    ServicedOrganisationWorkingDays,
    ServiceLink,
    ServicePattern,
    StopActivity,
    StopPoint,
    VehicleJourney,
    Tracks,
    TracksVehicleJourney,
)

ServicePatternThrough = ServicePattern.service_links.through
logger = logging.getLogger(__name__)


def create_naptan_flexible_zone_df_from_queryset(queryset):
    """
    Converts the naptan flexible zone table query set to pandas dataframe object
    and converts the flexible location geometry to list for same naptan stop points
    """
    flexible_zone = (
        {
            "naptan_id": obj.naptan_stoppoint_id,
            "flexible_location": Point(obj.location.x, obj.location.y),
            "sequence_number": obj.sequence_number,
        }
        for obj in queryset
    )
    df = create_flexible_zone_df(flexible_zone)
    # perform grouping of data on naptan_id and create list of flexible zone geometry
    if not df.empty:
        df = df.groupby(["naptan_id"])["flexible_location"].agg(list).reset_index()
    return df


def create_flexible_zone_df(data=None):
    """
    Converts the list of object to geopandas dataframe
    """
    typings = OrderedDict(
        {
            "naptan_id": "object",
            "flexible_location": "geometry",
            "sequence_number": "int",
        }
    )
    df = geopandas.GeoDataFrame(data, columns=typings.keys()).astype(typings)
    return df


def get_stop_activities():
    return StopActivity.objects.all()


def create_stop_point_cache(revision_id):
    stops = (
        StopPoint.objects.filter(
            service_pattern_stops__service_pattern__revision_id=revision_id
        )
        .distinct("id")
        .order_by("id")
    )
    return create_naptan_stoppoint_df_from_queryset(stops)


def create_txc_file_attributes_df(queryset: QuerySet) -> pd.DataFrame:
    """
    Creates dataframe from queryset
    """
    df_txc_file_attributes = pd.DataFrame.from_records(queryset.values())

    return df_txc_file_attributes


def filter_redundant_files(df: pd.DataFrame) -> pd.DataFrame:
    """Filters out files for the same service code which have lower revision number but the start date is greater than the highest revision file"""
    max_revision = df["revision_number"].max()
    df_max_revision_number = df[df["revision_number"] == max_revision]
    max_start_date = df_max_revision_number["operating_period_start_date"].max()
    df_filtered = df[
        (
            (df["operating_period_start_date"] < max_start_date)
            & (df["revision_number"] <= max_revision)
        )
        | (
            (df["operating_period_start_date"] == max_start_date)
            & (df["revision_number"] == max_revision)
        )
    ]
    return df_filtered[["id", "filename"]]


def get_txc_files(revision_id: int) -> pd.DataFrame:
    """Returns the valid txc files that should be processed for timetable visualiser based on their service code and operating start date"""
    txc_files = TXCFileAttributes.objects.filter(revision_id=revision_id)
    df_txc_files = create_txc_file_attributes_df(txc_files)
    columns = [
        "id",
        "service_code",
        "revision_number",
        "operating_period_start_date",
        "filename",
    ]
    df_with_valid_files = pd.DataFrame()
    if not df_txc_files.empty:
        df_txc_files = df_txc_files[columns]
        df_with_valid_files = df_txc_files.groupby("service_code").apply(
            filter_redundant_files
        )

    return df_with_valid_files


def create_service_link_cache(revision_id):
    service_links = ServiceLink.objects.filter(
        service_patterns__revision_id=revision_id
    ).distinct()

    return create_service_link_df_from_queryset(service_links)


def create_naptan_stoppoint_df(data=None):
    # Note id is float64 as it may contain missing values
    typings = OrderedDict(
        {
            "naptan_id": "object",
            "atco_code": "object",
            "geometry": "geometry",
            "locality_id": "str",
        }
    )
    return geopandas.GeoDataFrame(data, columns=typings.keys()).set_index(
        "atco_code", verify_integrity=True
    )


def create_naptan_stoppoint_df_from_queryset(queryset):
    stop_points = (
        {
            "naptan_id": obj.id,
            "atco_code": obj.atco_code,
            "locality_id": obj.locality_id,
            "geometry": Point(obj.location.x, obj.location.y),
        }
        for obj in queryset
    )
    return create_naptan_stoppoint_df(stop_points)


def create_service_df(data=None):
    columns = ["id", "service_code", "start_date", "end_date"]
    return pd.DataFrame(data, columns=columns).set_index(
        "service_code", verify_integrity=True
    )


def create_service_df_from_queryset(queryset):
    return create_service_df(
        (
            {
                "id": obj.id,
                "service_code": obj.service_code,
                "start_date": obj.start_date,
                "end_date": obj.end_date,
            }
            for obj in queryset
        )
    )


def create_service_link_df(data=None):
    columns = OrderedDict(
        {
            "id": "float64",
            "from_stop_atco": "object",
            "to_stop_atco": "object",
            "from_stop_id": "float64",
            "to_stop_id": "float64",
        }
    )
    return (
        pd.DataFrame(data, columns=columns.keys())
        .astype(columns)
        .set_index(["from_stop_atco", "to_stop_atco"], verify_integrity=True)
    )  # using a multiindex makes selections easier


def create_service_link_df_from_queryset(qs):
    return create_service_link_df(
        (
            {
                "id": obj.id,
                "from_stop_atco": obj.from_stop_atco,
                "to_stop_atco": obj.to_stop_atco,
                "from_stop_id": obj.from_stop_id,
                "to_stop_id": obj.to_stop_id,
            }
            for obj in qs
        )
    )


def create_naptan_locality_df(data=None):
    # Note id is float64 as it may contain missing values
    columns = OrderedDict(
        {"locality_id": "str", "locality_name": "str", "admin_area_id": "object"}
    )
    return (
        pd.DataFrame(data, columns=columns.keys())
        .astype(columns)
        .set_index("locality_id", verify_integrity=True)
    )


def df_to_service_patterns(
    revision: DatasetRevision, df: pd.DataFrame
) -> Iterator[ServicePattern]:
    """
    Convert a pandas DataFrame to an iterator of ServicePattern objects.
    DataFrame is expected to have columns 'service_pattern_id' and 'geometry'.
    Additional columns 'line_name' and 'description' are optional.
    """
    for record in df.reset_index().to_dict("records"):
        yield ServicePattern(
            revision=revision,
            service_pattern_id=record["service_pattern_id"],
            geom=record["geometry"],
            line_name=record.get("line_name", None),
            description=record.get("description", None),
        )


def df_to_services(revision: DatasetRevision, df: pd.DataFrame) -> Iterator[Service]:
    for record in df.to_dict("records"):
        start_date = record["start_date"]
        if pd.isnull(start_date):
            start_date = None
        end_date = record["end_date"]
        if pd.isnull(end_date):
            end_date = None
        line_names = record["line_names"]
        service_type = record["service_type"]
        yield Service(
            revision=revision,
            service_code=record["service_code"],
            start_date=start_date,
            end_date=end_date,
            name=line_names[0],
            other_names=line_names[1:],
            service_type=service_type,
            txcfileattributes_id=record["txc_file_id"],
        )


def df_to_vehicle_journeys(df: pd.DataFrame) -> Iterator[VehicleJourney]:
    """Generator function to return vehicle journey records to be loaded into the table"""
    for record in df.to_dict("records"):
        service_pattern_id = record.get("id_service", None)
        if pd.isna(record["vj_departure_time"]):
            departure_time = None
        else:
            departure_time = str(record["vj_departure_time"]).split()[2]

        yield VehicleJourney(
            journey_code=record["journey_code"],
            start_time=departure_time,
            line_ref=record["line_ref"],
            direction=record["direction"],
            departure_day_shift=record["departure_day_shift"],
            service_pattern_id=service_pattern_id,
            block_number=record["block_number"],
        )


def df_to_tracks(df: pd.DataFrame) -> Iterator[Dict]:
    """Generator function to yield records as dictionaries after verifying with the Tracks model"""
    for record in df.to_dict("records"):
        # Verify with the Tracks model
        track = Tracks(
            from_atco_code=record["from_atco_code"],
            to_atco_code=record["to_atco_code"],
            geometry=record["geometry"],
            distance=record["distance"],
        )

        # If the model instance is valid, yield it as a dictionary
        yield {
            "from_atco_code": track.from_atco_code,
            "to_atco_code": track.to_atco_code,
            "geometry": track.geometry,
            "distance": track.distance,
        }


def merge_vj_tracks_df(
    tracks: pd.DataFrame, vehicle_journeys: pd.DataFrame, tracks_map: pd.DataFrame
) -> pd.DataFrame:
    """
    Merges vehicle_journeys and tracks DataFrames to get the relationship table.

    Args:
        tracks (pd.DataFrame): DataFrame containing track information.
        vehicle_journeys (pd.DataFrame): DataFrame containing vehicle journey information.
        tracks_map (pd.DataFrame): DataFrame containing the mapping of journey patterns to route links.

    Returns:
        pd.DataFrame: The merged DataFrame with track and vehicle journey information.
    """
    # Initial processing
    internal_vjs = vehicle_journeys.copy()
    tracks.reset_index(inplace=True)
    tracks_map.reset_index(inplace=True)

    # Explode the 'jp_ref' and 'rs_ref' columns along with their corresponding 'rs_order'
    tracks_map_extended = tracks_map.explode("jp_ref").explode(["rs_ref", "rs_order"])

    tracks_columns_to_keep = ["rl_ref", "rs_ref", "rl_order", "id", "file_id"]
    tracks = tracks[tracks_columns_to_keep]
    tracks.rename(columns={"id": "tracks_id"}, inplace=True)

    # Merge tracks DataFrame with the extended tracks_map DataFrame on 'rs_ref'
    merged_tracks_map = pd.merge(
        tracks, tracks_map_extended, on=["rs_ref", "file_id"], how="inner"
    )

    # Create 'sequence' column by combining 'rs_order' and 'rl_order'   
    merged_tracks_map["sequence"] = merged_tracks_map.groupby(["jp_ref", "file_id"]).cumcount()
    # Drop 'rl_order' and 'rs_order' columns as they are no longer needed
    merged_tracks_map.drop(["rl_order", "rs_order"], inplace=True, axis=1)
    # Extract jp_ref from journey_pattern_ref
    internal_vjs["jp_ref"] = internal_vjs["journey_pattern_ref"].apply(
        lambda x: x.split("-")[1]
    )
    internal_vjs_columns_to_keep = ["jp_ref", "id", "file_id"]
    internal_vjs = internal_vjs[internal_vjs_columns_to_keep]
    internal_vjs.rename(columns={"id": "vj_id"}, inplace=True)

    # Merge the merged_tracks_map DataFrame with the internal_vjs DataFrame on 'jp_ref'
    merged_vjs_tracks_map = pd.merge(
        merged_tracks_map, internal_vjs, on=["jp_ref", "file_id"], how="inner"
    )

    if merged_vjs_tracks_map.empty:
        return pd.DataFrame()
    # Drop nan from all columns
    df_cleaned = merged_vjs_tracks_map.dropna(axis=1, how="all")
    # Check for NaN values 
    if df_cleaned.size != merged_tracks_map.size:
        logger.warning(
            f"Merge_vj_tracks_df: NaN values found in the tracks extracted data"
        )
    return df_cleaned


def df_to_journeys_tracks(df: pd.DataFrame) -> Iterator[TracksVehicleJourney]:
    """
    Generator function returns Tracks vehice journey records to be loaded into the table.
    """
    for record in df.to_dict("records"):
        vehicle_journey_id = record["vj_id"]
        yield TracksVehicleJourney(
            vehicle_journey_id=vehicle_journey_id,
            tracks_id=record["tracks_id"],
            sequence_number=record["sequence"],
        )


def get_time_field_or_none(time_in_text):
    time_field = None
    if time_in_text:
        time_field = datetime.strptime(time_in_text, "%H:%M:%S").time()

    return time_field


def df_to_flexible_service_operation_period(
    df: pd.DataFrame,
) -> Iterator[FlexibleServiceOperationPeriod]:
    for record in df.to_dict("records"):
        yield FlexibleServiceOperationPeriod(
            vehicle_journey_id=record["id"],
            start_time=get_time_field_or_none(record["start_time"]),
            end_time=get_time_field_or_none(record["end_time"]),
        )


def df_to_serviced_organisations(
    df: pd.DataFrame, existing_serviced_orgs_list: List[str]
) -> Iterator[ServicedOrganisations]:
    """Compare the serviced organisation present in the database with the
    uploaded file based on name and org code"""

    unique_org_codes = df.drop_duplicates(
        subset=["serviced_org_ref", "name"], keep="first"
    )
    unique_org_codes["serviced_org_ref_name"] = df[["name", "serviced_org_ref"]].agg(
        "".join, axis=1
    )
    serviced_org_records = unique_org_codes[
        ~unique_org_codes["serviced_org_ref_name"].isin(existing_serviced_orgs_list)
    ]

    for record in serviced_org_records.to_dict("records"):
        yield ServicedOrganisations(
            organisation_code=record["serviced_org_ref"], name=record["name"]
        )


def df_to_serviced_organisation_working_days(
    df: pd.DataFrame, columns_to_drop_duplicates: list
) -> Iterator[ServicedOrganisationWorkingDays]:
    if not df.empty:
        df_to_load = df.reset_index()
        for record in df_to_load.drop_duplicates(
            subset=columns_to_drop_duplicates
        ).itertuples(index=False):
            yield ServicedOrganisationWorkingDays(
                serviced_organisation_vehicle_journey_id=record.serviced_org_vj_id,
                start_date=datetime.strptime(record.start_date, "%Y-%m-%d").date(),
                end_date=datetime.strptime(record.end_date, "%Y-%m-%d").date(),
            )


def df_to_operating_profiles(df: pd.DataFrame) -> Iterator[OperatingProfile]:
    for record in df.to_dict("records"):
        yield OperatingProfile(
            vehicle_journey_id=record["id"], day_of_week=record["day_of_week"]
        )


def df_to_serviced_org_vehicle_journey(
    df: pd.DataFrame,
) -> Iterator[ServicedOrganisationVehicleJourney]:
    for record in df.to_dict("records"):
        yield ServicedOrganisationVehicleJourney(
            vehicle_journey_id=record["vehicle_journey_id"],
            serviced_organisation_id=record["serviced_org_id"],
            operating_on_working_days=record["operational"],
        )


def df_to_operating_dates_exceptions(
    df: pd.DataFrame,
) -> Iterator[OperatingDatesExceptions]:
    for record in df.to_dict("records"):
        yield OperatingDatesExceptions(
            vehicle_journey_id=record["id"], operating_date=record["exceptions_date"]
        )


def df_to_non_operating_dates_exceptions(
    df: pd.DataFrame,
) -> Iterator[NonOperatingDatesExceptions]:
    for record in df.to_dict("records"):
        yield NonOperatingDatesExceptions(
            vehicle_journey_id=record["id"],
            non_operating_date=record["exceptions_date"],
        )


def df_to_service_links(df: pd.DataFrame) -> Iterator[ServiceLink]:
    for record in df.reset_index().to_dict("records"):
        from_stop_id = record["from_stop_id"]
        if pd.isnull(from_stop_id):
            from_stop_id = None
        to_stop_id = record["to_stop_id"]
        if pd.isnull(to_stop_id):
            to_stop_id = None
        yield ServiceLink(
            from_stop_atco=record["from_stop_atco"],
            to_stop_atco=record["to_stop_atco"],
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
        )


def df_to_service_pattern_service(
    df: pd.DataFrame,
) -> Iterator[ServicePatternThrough]:
    for record in df[["id", "service_link_id"]].to_dict("records"):
        yield ServicePatternThrough(
            servicepattern_id=record["id"], servicelink_id=record["service_link_id"]
        )


def db_bank_holidays_to_df(columns: List[str]) -> pd.DataFrame:
    db_bank_holidays = BankHolidays.objects.values(*columns)
    df_bank_holidays_from_db = pd.DataFrame(db_bank_holidays, columns=columns)
    df_bank_holidays_from_db.drop_duplicates(inplace=True)

    return df_bank_holidays_from_db


def get_first_and_last_expiration_dates(expiration_dates: list, start_dates: list):
    """Compute the first and last expiration dates (excluding '9999-09-09'
    which is declared as the default)"""
    first_expiring_service = None
    last_expiring_service = None
    first_service_start = None
    logger.info("[get_first_and_last_expiration_dates]:{start_dates}")
    for date in expiration_dates:
        if date:
            if first_expiring_service is None or date < first_expiring_service:
                first_expiring_service = date

            if last_expiring_service is None or date > last_expiring_service:
                last_expiring_service = date
    for date in start_dates:
        if date:
            if first_service_start is None or date < first_service_start:
                logger.info("[get_first_and_last_expiration_dates]:{date}")
                first_service_start = date
    return first_expiring_service, last_expiring_service, first_service_start


def get_min_date_or_none(dates):
    dates = [date for date in dates if date is not None]
    return min(dates) if dates else None


def get_max_date_or_none(dates):
    dates = [date for date in dates if date is not None]
    return max(dates) if dates else None


def df_to_booking_arrangements(
    revision: DatasetRevision, df: pd.DataFrame
) -> Iterator[BookingArrangements]:
    for record in df.reset_index().to_dict("records"):
        service_id = record["id"]

        yield BookingArrangements(
            service_id=service_id,
            description=record["description"],
            email=record["email"],
            phone_number=record["tel_national_number"],
            web_address=record["web_address"],
        )
