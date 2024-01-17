from celery.utils.log import get_task_logger
from django.contrib.gis.geos import Point

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.naptan.models import AdminArea, FlexibleZone, Locality, StopPoint

logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)


def load_new_stops(new_stops):
    logger.info(f"Loading {len(new_stops)} new NaPTAN StopPoints.")
    stops_list = []
    for row in new_stops.itertuples():
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
    StopPoint.objects.bulk_create(stops_list, batch_size=5000)
    logger.info("Finished loading new StopPoints.")


def load_flexible_zone(flexible_stops):
    logger.info("[load_flexible_zone]: Started")
    for row in flexible_stops.itertuples():
        flexible_sequence_number = 0
        for flexible_location in row.flexible_location.location:
            flexible_sequence_number += 1
            FlexibleZone.objects.update_or_create(
                sequence_number=flexible_sequence_number,
                naptan_stoppoint_id=row.obj.id,
                defaults={
                    "sequence_number": flexible_sequence_number,
                    "naptan_stoppoint_id": row.obj.id,
                    "location": Point(
                        x=float(flexible_location.translation.longitude),
                        y=float(flexible_location.translation.latitude),
                        srid=4326,
                    ),
                },
            )
    logger.info("[load_flexible_zone]: Finished")


def load_existing_stops(existing_stops):
    logger.info("Loading existing NaPTAN stops.")
    for row in existing_stops.itertuples():
        obj = row.obj
        obj.atco_code = row.Index
        obj.naptan_code = row.naptan_code
        obj.common_name = row.common_name
        obj.indicator = row.indicator
        obj.street = row.street
        obj.locality_id = row.locality_id
        obj.admin_area_id = int(row.admin_area_id)
        obj.location = Point(x=float(row.longitude), y=float(row.latitude), srid=4326)
        obj.stop_areas = row.stop_areas
        obj.stop_type = row.stop_type
        obj.bus_stop_type = row.bus_stop_type

    StopPoint.objects.bulk_update(
        existing_stops["obj"],
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
        batch_size=5000,
    )
    logger.info(f"Finished loading {len(existing_stops)} existing NaPTAN stops.")


def load_new_admin_areas(new_admin_areas):
    logger.info("[load_new_admin_areas]: Started")
    admin_areas_list = []
    for row in new_admin_areas.itertuples():
        admin_areas_list.append(
            AdminArea(
                id=int(row.Index),
                name=row.name,
                traveline_region_id=row.traveline_region_id,
                atco_code=row.atco_code,
            )
        )

    AdminArea.objects.bulk_create(admin_areas_list, batch_size=100)
    logger.info("[load_new_admin_areas]: Finished")


def load_existing_admin_areas(existing_admin_areas):
    logger.info("[load_existing_admin_areas]: Started")
    for row in existing_admin_areas.itertuples():
        obj = row.obj
        obj.id = int(row.Index)
        obj.name = row.name
        obj.traveline_region_id = row.traveline_region_id
        obj.atco_code = row.atco_code

    AdminArea.objects.bulk_update(
        existing_admin_areas["obj"],
        (
            "name",
            "traveline_region_id",
            "atco_code",
        ),
        batch_size=100,
    )
    logger.info("[load_existing_admin_areas]: Finished")


def load_new_localities(new_localities):
    logger.info("[load_new_localities]: Started")
    localities_list = []
    for row in new_localities.itertuples():
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

    Locality.objects.bulk_create(localities_list, batch_size=5000)
    logger.info("[load_new_localities]: Finished")


def load_existing_localities(existing_localities):
    logger.info("[load_existing_localities]: Started")
    for row in existing_localities.itertuples():
        obj = row.obj
        obj.gazetteer_id = row.Index
        obj.name = row.name
        obj.easting = row.easting
        obj.northing = row.northing
        # obj.district_id = int(row.district_id)
        obj.admin_area_id = int(row.admin_area_id)

    Locality.objects.bulk_update(
        existing_localities["obj"],
        ("name", "easting", "northing", "district_id", "admin_area_id"),
        batch_size=5000,
    )
    logger.info("[load_existing_localities]: Finished")
