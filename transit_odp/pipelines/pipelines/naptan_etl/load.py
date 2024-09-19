from celery.utils.log import get_task_logger
from django.contrib.gis.geos import Point
from django.db import IntegrityError, transaction

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.naptan.models import AdminArea, FlexibleZone, Locality, StopPoint
from transit_odp.pipelines.pipelines.naptan_etl.transform import (
    extract_flexible_zones_from_db,
    extract_flexible_zones_from_df,
    get_flexible_zones_in_both,
    get_flexible_zones_in_db_only,
    get_flexible_zones_in_xml_only,
)

logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)


def load_new_stops(new_stops):
    logger.info(f"[load_new_stops]: Loading {len(new_stops)} new NaPTAN StopPoints.")
    chunk_size = 5000
    total_rows = len(new_stops)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = new_stops.iloc[start:end]
        stops_list = []
        for row in chunk.itertuples():
            stops_list.append(
                StopPoint(
                    atco_code=row.Index,
                    naptan_code=row.naptan_code,
                    common_name=row.common_name,
                    indicator=row.indicator,
                    street=row.street,
                    locality_id=row.locality_id,
                    admin_area_id=row.admin_area_id,
                    location=Point(
                        x=float(row.longitude), y=float(row.latitude), srid=4326
                    ),
                    stop_areas=row.stop_areas,
                    stop_type=row.stop_type,
                    bus_stop_type=row.bus_stop_type,
                )
            )
        try:
            with transaction.atomic():
                StopPoint.objects.bulk_create(stops_list)
        except IntegrityError as e:
            logger.error(
                f"[load_new_stops]: Error processing rows {start} to {end} - {e}"
            )
        logger.info(f"[load_new_stops]: Processed rows {start} to {end}")
    logger.info("[load_new_stops]: Finished loading new StopPoints.")


def load_existing_stops(existing_stops):
    logger.info(
        f"[load_existing_stops]: Loading {len(existing_stops)} existing NaPTAN stops."
    )
    chunk_size = 2000
    total_rows = len(existing_stops)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = existing_stops.iloc[start:end]
        objs = []
        for row in chunk.itertuples():
            obj = row.obj
            obj.atco_code = row.Index
            obj.naptan_code = row.naptan_code
            obj.common_name = row.common_name
            obj.indicator = row.indicator
            obj.street = row.street
            obj.locality_id = row.locality_id
            obj.admin_area_id = int(row.admin_area_id)
            obj.location = Point(
                x=float(row.longitude), y=float(row.latitude), srid=4326
            )
            obj.stop_areas = row.stop_areas
            obj.stop_type = row.stop_type
            obj.bus_stop_type = row.bus_stop_type
            objs.append(obj)
        try:
            with transaction.atomic():
                StopPoint.objects.bulk_update(
                    objs,
                    (
                        "atco_code",
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
                    ),
                )
        except Exception as e:
            logger.error(
                f"[load_existing_stops]: Error processing rows {start} to {end} - {e}"
            )
        logger.info(f"[load_existing_stops]: Processed rows {start} to {end}")
    logger.info(
        f"[load_existing_stops]: Finished loading {total_rows} existing NaPTAN stops."
    )


def load_new_admin_areas(new_admin_areas):
    logger.info(
        f"[load_new_admin_areas]: Loading {len(new_admin_areas)} new admin areas"
    )
    chunk_size = 5000
    total_rows = len(new_admin_areas)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = new_admin_areas.iloc[start:end]

        admin_areas_list = []
        for row in chunk.itertuples():
            admin_areas_list.append(
                AdminArea(
                    id=int(row.Index),
                    name=row.name,
                    traveline_region_id=row.traveline_region_id,
                    atco_code=row.atco_code,
                )
            )
        try:
            with transaction.atomic():
                AdminArea.objects.bulk_create(admin_areas_list)
        except Exception as exp:
            logger.error(
                f"[load_new_admin_areas]: Error processing rows {start} to {end} - {exp}"
            )
        logger.info(f"[load_new_admin_areas]: Processed rows {start} to {end}")
    logger.info("[load_new_admin_areas]: Finished")


def load_existing_admin_areas(existing_admin_areas):
    logger.info(
        f"[load_existing_admin_areas]: Loading {len(existing_admin_areas)} existing admin areas"
    )
    chunk_size = 5000
    total_rows = len(existing_admin_areas)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = existing_admin_areas.iloc[start:end]
        objs = []
        for row in chunk.itertuples():
            obj = row.obj
            obj.id = int(row.Index)
            obj.name = row.name
            obj.traveline_region_id = row.traveline_region_id
            obj.atco_code = row.atco_code
            objs.append(obj)
        try:
            with transaction.atomic():
                AdminArea.objects.bulk_update(
                    objs,
                    (
                        "name",
                        "traveline_region_id",
                        "atco_code",
                    ),
                )
        except Exception as exp:
            logger.error(
                f"[load_existing_admin_areas]: Error processing rows {start} to {end} - {exp}"
            )
        logger.info(f"[load_existing_admin_areas]: Processed rows {start} to {end}")
    logger.info("[load_existing_admin_areas]: Finished")


def load_new_localities(new_localities):
    logger.info(f"[load_new_localities]: Loading {len(new_localities)} new localities")
    chunk_size = 5000
    total_rows = len(new_localities)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = new_localities.iloc[start:end]
        localities_list = []
        for row in chunk.itertuples():
            localities_list.append(
                Locality(
                    gazetteer_id=row.Index,
                    name=row.name,
                    easting=row.easting,
                    northing=row.northing,
                    # district_id=int(row.district_id),
                    admin_area_id=int(row.admin_area_id),
                )
            )
        try:
            with transaction.atomic():
                Locality.objects.bulk_create(localities_list)
        except Exception as e:
            logger.error(
                f"[load_new_localities]: Error processing rows {start} to {end} - {e}"
            )
        logger.info(f"[load_new_localities]: Processed rows {start} to {end}")
    logger.info("[load_new_localities]: Finished")


def load_existing_localities(existing_localities):
    logger.info(
        f"[load_existing_localities]: Loading {len(existing_localities)} existing localities"
    )
    chunk_size = 5000
    total_rows = len(existing_localities)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = existing_localities.iloc[start:end]
        objs = []
        for row in chunk.itertuples():
            obj = row.obj
            obj.gazetteer_id = row.Index
            obj.name = row.name
            obj.easting = row.easting
            obj.northing = row.northing
            # obj.district_id = int(row.district_id)
            obj.admin_area_id = int(row.admin_area_id)
            objs.append(obj)
        try:
            with transaction.atomic():
                Locality.objects.bulk_update(
                    objs,
                    ("name", "easting", "northing", "district_id", "admin_area_id"),
                )
            logger.info(f"[load_existing_localities]: Processed rows {start} to {end}")
        except Exception as exp:
            logger.error(
                f"[load_existing_localities]: Error processing rows {start} to {end} - {e}"
            )
    logger.info("[load_existing_localities]: Finished")


def create_flexible_zones(flexible_zones):
    logger.info(
        f"[create_flexible_zones]: Loading {len(flexible_zones)} new flexible zones"
    )
    chunk_size = 5000
    total_rows = len(flexible_zones)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = flexible_zones.iloc[start:end]
        flexible_zones_list = []
        for index, flexible_zone in chunk.iterrows():
            flexible_zones_list.append(
                FlexibleZone(
                    sequence_number=index[0],
                    naptan_stoppoint_id=index[1],
                    location=Point(
                        x=float(flexible_zone["zone_df"].translation.longitude),
                        y=float(flexible_zone["zone_df"].translation.latitude),
                        srid=4326,
                    ),
                )
            )
        try:
            with transaction.atomic():
                FlexibleZone.objects.bulk_create(flexible_zones_list)
        except Exception as e:
            logger.error(
                f"[create_flexible_zones]: Error processing rows {start} to {end} - {e}"
            )
        logger.info(f"[create_flexible_zones]: Processed rows {start} to {end}")
    logger.info("[create_flexible_zones]: Finished creating new Flexible Zones.")


def update_flexible_zones(flexible_zones):
    logger.info(
        f"[update_flexible_zones]: Updating {len(flexible_zones)} existing flexible zones"
    )

    chunk_size = 5000
    total_rows = len(flexible_zones)

    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = flexible_zones.iloc[start:end]

        flexible_zones_list = []
        for index, flexible_zone in chunk.iterrows():
            flexible_zones_list.append(
                FlexibleZone(
                    id=flexible_zone["zone_db"].id,
                    sequence_number=index[0],
                    naptan_stoppoint_id=index[1],
                    location=Point(
                        x=float(flexible_zone["zone_df"].translation.longitude),
                        y=float(flexible_zone["zone_df"].translation.latitude),
                        srid=4326,
                    ),
                )
            )
        try:
            with transaction.atomic():
                FlexibleZone.objects.bulk_update(
                    flexible_zones_list,
                    fields=["sequence_number", "naptan_stoppoint_id", "location"],
                )
        except Exception as e:
            logger.error(
                f"[update_flexible_zones]: Error processing rows {start} to {end} - {e}"
            )
        logger.info(f"[update_flexible_zones]: Processed rows {start} to {end}")
    logger.info("[update_flexible_zones]: Finished updating existing Flexible Zones")


def delete_flexible_zones(flexible_zones):
    logger.info(
        f"[delete_flexible_zones]: Deleting {len(flexible_zones)} existing flexible zones"
    )
    chunk_size = 5000
    total_rows = len(flexible_zones)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = flexible_zones.iloc[start:end]
        ids_to_delete = [
            flexible_zone["zone_db"].id for _index, flexible_zone in chunk.iterrows()
        ]
        if ids_to_delete:
            try:
                FlexibleZone.objects.filter(id__in=ids_to_delete).delete()
                logger.info(
                    f"[delete_flexible_zones]: Deleted {len(ids_to_delete)} Flexible Zones in rows {start} to {end}"
                )
            except Exception as e:
                logger.error(
                    f"[delete_flexible_zones]: Error deleting rows {start} to {end} - {e}"
                )
        else:
            logger.info(
                f"[delete_flexible_zones]: No records to delete in rows {start} to {end}"
            )
    logger.info("[delete_flexible_zones]: Finished deleting Flexible Zones")


def load_flexible_zones(all_flexible_stops):
    logger.info(f"[load_flexible_zones]: Started")
    try:
        flexible_zones_from_db = extract_flexible_zones_from_db()
        flexible_zones_from_df = extract_flexible_zones_from_df(all_flexible_stops)

        flexible_zones_to_create = get_flexible_zones_in_xml_only(
            flexible_zones_from_db, flexible_zones_from_df
        )
        flexible_zones_update = get_flexible_zones_in_both(
            flexible_zones_from_db, flexible_zones_from_df
        )
        flexible_zones_to_delete = get_flexible_zones_in_db_only(
            flexible_zones_from_db, flexible_zones_from_df
        )
        if not flexible_zones_to_create.empty:
            logger.info(
                f"[load_flexible_zones]: Creating {len(flexible_zones_to_create)} new Flexible Zones"
            )
            create_flexible_zones(flexible_zones_to_create)
        if not flexible_zones_update.empty:
            logger.info(
                f"[load_flexible_zones]: Updating {len(flexible_zones_update)} Flexible Zones"
            )
            update_flexible_zones(flexible_zones_update)
        if not flexible_zones_to_delete.empty:
            logger.info(
                f"[load_flexible_zones]: Deleting {len(flexible_zones_to_delete)} Flexible Zones"
            )
            delete_flexible_zones(flexible_zones_to_delete)
    except Exception as e:
        logger.error(f"[load_flexible_zones]: Error occurred - {e}")
    logger.info("[load_flexible_zones]: Finished")


def delete_existing_stops(stops):
    logger.info(f"[delete_existing_stops]: Deleting {len(stops)} existing naptan stops")
    chunk_size = 5000
    total_rows = len(stops)
    for start in range(0, total_rows, chunk_size):
        end = min(start + chunk_size, total_rows)
        chunk = stops.iloc[start:end]
        atcos_to_delete = list(chunk.index)
        if atcos_to_delete:
            try:
                # first delete flexible zones for naptan_stoppoint id's then delete the stoppoint
                naptan_ids = set(
                    StopPoint.objects.filter(atco_code__in=atcos_to_delete).values_list(
                        "id", flat=True
                    )
                )
                FlexibleZone.objects.filter(naptan_stoppoint__in=naptan_ids).delete()
                StopPoint.objects.filter(id__in=naptan_ids).delete()
                logger.info(
                    f"[delete_existing_stops]: Deleted {len(atcos_to_delete)} naptan stops in rows {start} to {end}"
                )
            except Exception as e:
                logger.error(
                    f"[delete_existing_stops]: Error deleting rows {start} to {end} - {e}"
                )
        else:
            logger.info(
                f"[delete_existing_stops]: No records to delete in rows {start} to {end}"
            )
    logger.info("[delete_existing_stops]: Finished deleting existing stops")
