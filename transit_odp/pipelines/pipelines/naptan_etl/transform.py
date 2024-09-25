import pandas as pd
from celery.utils.log import get_task_logger
from django.contrib.gis.geos import Point

from transit_odp.naptan.models import (
    AdminArea,
    District,
    FlexibleZone,
    Locality,
    StopPoint,
)

logger = get_task_logger(__name__)


def extract_stops_from_db():
    def inner():
        for stop in StopPoint.objects.all():
            yield {"atco_code": stop.atco_code, "obj": stop}

    df = pd.DataFrame(
        inner(),
        columns=["atco_code", "obj"],
    ).set_index("atco_code")
    return df


def extract_admin_areas_from_db():
    def inner():
        for admin_area in AdminArea.objects.all():
            yield {"id": admin_area.id, "obj": admin_area}

    df = pd.DataFrame(
        inner(),
        columns=["id", "obj"],
    ).set_index("id")
    return df


def extract_districts_from_db():
    def inner():
        for district in District.objects.all():
            yield {"id": district.id, "obj": district}

    df = pd.DataFrame(
        inner(),
        columns=["id", "obj"],
    ).set_index("id")
    return df


def extract_localities_from_db():
    def inner():
        for locality in Locality.objects.all():
            yield {"gazetteer_id": locality.gazetteer_id, "obj": locality}

    df = pd.DataFrame(
        inner(),
        columns=["gazetteer_id", "obj"],
    ).set_index("gazetteer_id")
    return df


def get_new_data(naptan_data, db_data):
    intersection = naptan_data[~naptan_data.index.isin(db_data.index)]
    return intersection


def get_existing_data(naptan_data, db_data, merge_on_field):
    existing_data = pd.merge(naptan_data, db_data, how="inner", on=merge_on_field)
    return existing_data


def extract_flexible_zones_from_db():
    def inner():
        for zone in FlexibleZone.objects.all():
            yield {
                "sequence_number": zone.sequence_number,
                "naptan_stoppoint_id": zone.naptan_stoppoint_id,
                "zone_db": zone,
            }

    df = pd.DataFrame(
        inner(),
        columns=["sequence_number", "naptan_stoppoint_id", "zone_db"],
    ).set_index(["sequence_number", "naptan_stoppoint_id"])
    return df


def extract_flexible_zones_from_df(stop_points):
    def inner():
        for stop_point in stop_points.itertuples():
            if stop_point.flexible_zones is not None:
                for sequence, flexible_zone in enumerate(
                    stop_point.flexible_zones.location
                ):
                    yield {
                        "sequence_number": sequence + 1,
                        "naptan_stoppoint_id": stop_point.obj.id,
                        "zone_df": flexible_zone,
                    }

    df = pd.DataFrame(
        inner(),
        columns=["sequence_number", "naptan_stoppoint_id", "zone_df"],
    ).set_index(["sequence_number", "naptan_stoppoint_id"])
    return df


def get_flexible_zones_in_xml_only(flexible_zones_from_db, flexible_zones_from_df):
    merged = flexible_zones_from_df.merge(
        flexible_zones_from_db,
        how="outer",
        indicator=True,
        on=["sequence_number", "naptan_stoppoint_id"],
    )
    return merged[merged["_merge"] == "left_only"]


def get_flexible_zones_in_both(flexible_zones_from_db, flexible_zones_from_df):
    existing_data = pd.merge(
        flexible_zones_from_db,
        flexible_zones_from_df,
        how="inner",
        indicator=True,
        on=["sequence_number", "naptan_stoppoint_id"],
    )
    return existing_data


def get_flexible_zones_in_db_only(flexible_zones_from_db, flexible_zones_from_df):
    merged = flexible_zones_from_db.merge(
        flexible_zones_from_df,
        how="outer",
        indicator=True,
        on=["sequence_number", "naptan_stoppoint_id"],
    )
    return merged[merged["_merge"] == "left_only"]


def drop_stops_with_invalid_admin_areas(
    stops: pd.DataFrame, admin_areas: pd.DataFrame
) -> pd.DataFrame:
    bad_stops = stops[~stops.admin_area_id.isin(admin_areas.index)]
    bad_count = len(bad_stops)
    if bad_count:
        bad_admin_areas = bad_stops.admin_area_id.unique()
        bad_codes = ", ".join(str(code) for code in bad_admin_areas)
        logger.warning(
            f"Found {bad_count} with incorrect admin area codes {bad_codes}."
        )

    good_stops = stops[stops.admin_area_id.isin(admin_areas.index)]
    return good_stops


def drop_stops_with_invalid_localities(
    stops: pd.DataFrame, localities: pd.DataFrame
) -> pd.DataFrame:
    bad_stops = stops[~stops.locality_id.isin(localities.index)]
    bad_count = len(bad_stops)
    if bad_count:
        bad_ids = ", ".join(str(code) for code in bad_stops.locality_id.unique())
        logger.warning(f"Found {bad_count} with incorrect locality ids {bad_ids}.")

    good_stops = stops[stops.locality_id.isin(localities.index)]
    return good_stops


def get_records_to_update(dataframe, columns_to_check, create_location=False):
    def check_update(row):
        obj = row.get("obj")
        if obj is None:
            return None

        for col in columns_to_check:
            if col in row and hasattr(obj, col):
                if row[col] != getattr(obj, col):
                    return "Yes"
        return "No"

    df_copy = dataframe.copy()
    if (
        create_location
        and "longitude" in df_copy.columns
        and "latitude" in df_copy.columns
    ):
        df_copy["location"] = df_copy.apply(
            lambda row: Point(
                float(row["longitude"]), float(row["latitude"]), srid=4326
            ),
            axis=1,
        )
    df_copy["is_update"] = df_copy.apply(check_update, axis=1)
    df_copy["is_update"] = df_copy["is_update"].replace({None: "", "No": ""})
    df_copy = df_copy[df_copy["is_update"] == "Yes"]
    cols_to_drop = ["is_update", "location"] if create_location else ["is_update"]
    df_copy.drop(cols_to_drop, axis=1, inplace=True, errors="ignore")
    return df_copy


def get_stops_to_update(stoppoints):
    columns_to_check = [
        "naptan_code",
        "common_name",
        "indicator",
        "street",
        "locality_id",
        "admin_area_id",
        "location",
        "stop_areas",
        "stop_type",
        "bus_stop_type",
    ]
    return get_records_to_update(stoppoints, columns_to_check, create_location=True)


def get_admin_areas_to_update(admin_areas):
    columns_to_check = ["name", "traveline_region_id", "atco_code"]
    return get_records_to_update(admin_areas, columns_to_check)


def get_localities_to_update(localities):
    columns_to_check = ["name", "easting", "northing", "admin_area_id"]
    return get_records_to_update(localities, columns_to_check)
