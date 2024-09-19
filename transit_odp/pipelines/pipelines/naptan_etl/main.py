import pandas as pd
from celery.utils.log import get_task_logger

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.pipelines.pipelines.naptan_etl.extract import (
    cleanup,
    extract_admin_areas,
    extract_localities,
    extract_stops,
    get_latest_naptan_xml,
    get_latest_nptg,
)
from transit_odp.pipelines.pipelines.naptan_etl.load import (
    delete_existing_stops,
    load_existing_admin_areas,
    load_existing_localities,
    load_existing_stops,
    load_flexible_zones,
    load_new_admin_areas,
    load_new_localities,
    load_new_stops,
)
from transit_odp.pipelines.pipelines.naptan_etl.transform import (
    drop_stops_with_invalid_admin_areas,
    drop_stops_with_invalid_localities,
    extract_admin_areas_from_db,
    extract_districts_from_db,
    extract_localities_from_db,
    extract_stops_from_db,
    get_existing_data,
    get_new_data,
)

logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)


def run():
    logger.info("Running NaPTAN loading pipeline.")

    naptan_file_path = get_latest_naptan_xml()
    nptg_file_path = get_latest_nptg()

    stops_naptan = extract_stops(naptan_file_path)

    admin_areas_naptan = extract_admin_areas(nptg_file_path)
    localities_naptan = extract_localities(nptg_file_path)

    stops_naptan = drop_stops_with_invalid_admin_areas(stops_naptan, admin_areas_naptan)
    stops_naptan = drop_stops_with_invalid_localities(stops_naptan, localities_naptan)
    # Extract all data from DB
    stops_from_db = extract_stops_from_db()
    admin_areas_from_db = extract_admin_areas_from_db()
    extract_districts_from_db()
    localities_from_db = extract_localities_from_db()

    # delete stops that are not found in NAPTAN.xml but present in database
    stops_to_delete = stops_from_db.loc[
        stops_from_db.index.difference(stops_naptan.index)
    ]
    delete_existing_stops(stops_to_delete)

    # Transform
    new_stops = get_new_data(stops_naptan, stops_from_db)
    existing_stops = get_existing_data(stops_naptan, stops_from_db, "atco_code")
    new_admin_areas = get_new_data(admin_areas_naptan, admin_areas_from_db)
    existing_admin_areas = get_existing_data(
        admin_areas_naptan, admin_areas_from_db, "id"
    )
    new_localities = get_new_data(localities_naptan, localities_from_db)
    existing_localities = get_existing_data(
        localities_naptan, localities_from_db, "gazetteer_id"
    )

    logger.info(f"[naptan_etl: run]: New admin_areas {len(new_admin_areas)} found")
    load_new_admin_areas(new_admin_areas)
    load_existing_admin_areas(existing_admin_areas)

    logger.info(f"[naptan_etl: run]: New localities {len(new_localities)} found")
    load_new_localities(new_localities)
    load_existing_localities(existing_localities)

    logger.info(f"[naptan_etl: run]: New stops {len(new_stops)} found")
    load_new_stops(new_stops)
    load_existing_stops(existing_stops)

    stops_from_db = extract_stops_from_db()
    new_flexible_stop_points = new_stops[~new_stops["flexible_zones"].isna()]
    new_flexible_stops = get_existing_data(
        new_flexible_stop_points, stops_from_db, merge_on_field="atco_code"
    )
    existing_flexible_stops = existing_stops[~existing_stops["flexible_zones"].isna()]
    all_flexible_stops = pd.concat([new_flexible_stops, existing_flexible_stops])
    load_flexible_zones(all_flexible_stops)

    cleanup()
    logger.info("[run] finished")
