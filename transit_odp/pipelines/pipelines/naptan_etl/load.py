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
        updates = []
        for row in chunk.itertuples():
            updates.append(
                {
                    "id": row.obj.id,
                    "atco_code": row.obj.atco_code,
                    "naptan_code": row.obj.naptan_code,
                    "common_name": row.obj.common_name,
                    "indicator": row.obj.indicator,
                    "street": row.obj.street,
                    "locality_id": row.obj.locality_id,
                    "admin_area_id": row.obj.admin_area_id,
                    "location": row.obj.location,
                    "stop_areas": row.obj.stop_areas,
                    "stop_type": row.obj.stop_type,
                    "bus_stop_type": row.obj.bus_stop_type,
                }
            )
        try:
            with transaction.atomic():
                for update in updates:
                    StopPoint.objects.filter(id=update["id"]).update(
                        atco_code=update["atco_code"],
                        naptan_code=update["naptan_code"],
                        common_name=update["common_name"],
                        indicator=update["indicator"],
                        street=update["street"],
                        locality_id=update["locality_id"],
                        admin_area_id=update["admin_area_id"],
                        location=Point(
                            x=update["location"].x, y=update["location"].y, srid=4326
                        ),
                        stop_areas=update["stop_areas"],
                        stop_type=update["stop_type"],
                        bus_stop_type=update["bus_stop_type"],
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
        updates = []
        for row in chunk.itertuples():
            updates.append(
                {
                    "id": int(row.Index),
                    "name": row.name,
                    "traveline_region_id": row.traveline_region_id,
                    "atco_code": row.atco_code,
                }
            )

        try:
            with transaction.atomic():
                for update in updates:
                    AdminArea.objects.filter(id=update["id"]).update(
                        name=update["name"],
                        traveline_region_id=update["traveline_region_id"],
                        atco_code=update["atco_code"],
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
        updates = []
        for row in chunk.itertuples():
            updates.append(
                {
                    "gazetteer_id": row.Index,
                    "name": row.name,
                    "easting": row.easting,
                    "northing": row.northing,
                    "admin_area_id": int(row.admin_area_id),
                }
            )
        try:
            with transaction.atomic():
                for update in updates:
                    Locality.objects.filter(gazetteer_id=update["gazetteer_id"]).update(
                        name=update["name"],
                        easting=update["easting"],
                        northing=update["northing"],
                        admin_area_id=update["admin_area_id"],
                    )
        except Exception as exp:
            logger.error(
                f"[load_existing_localities]: Error processing rows {start} to {end} - {exp}"
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
        updates = []
        for index, flexible_zone in chunk.iterrows():
            updates.append(
                {
                    "id": flexible_zone["zone_db"].id,
                    "sequence_number": index[0],
                    "naptan_stoppoint_id": index[1],
                    "location": Point(
                        x=float(flexible_zone["zone_df"].translation.longitude),
                        y=float(flexible_zone["zone_df"].translation.latitude),
                        srid=4326,
                    ),
                }
            )
        try:
            with transaction.atomic():
                for update in updates:
                    FlexibleZone.objects.filter(id=update["id"]).update(
                        sequence_number=update["sequence_number"],
                        naptan_stoppoint_id=update["naptan_stoppoint_id"],
                        location=update["location"],
                    )
        except Exception as exp:
            logger.error(
                f"[load_existing_localities]: Error processing rows {start} to {end} - {exp}"
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
