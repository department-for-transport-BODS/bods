from celery.utils.log import get_task_logger

from transit_odp.pipelines.pipelines.naptan_etl.extract import (
    cleanup,
    extract_admin_areas,
    extract_localities,
    extract_stops,
    get_latest_naptan_xml,
    get_latest_nptg,
)
from transit_odp.pipelines.pipelines.naptan_etl.load import (
    load_existing_admin_areas,
    load_existing_localities,
    load_existing_stops,
    load_new_admin_areas,
    load_new_localities,
    load_new_stops,
)
from transit_odp.pipelines.pipelines.naptan_etl.transform import (
    extract_admin_areas_from_db,
    extract_districts_from_db,
    extract_localities_from_db,
    extract_stops_from_db,
    get_existing_data,
    get_new_data,
)

logger = get_task_logger(__name__)


def run():
    logger.info("[run] called")
    # Note this task requires the set_expired_datasets task to run first to ensure the
    # bulk download is consistent.
    # TODO We could create a higher-level Celery task to run the series of tasks in
    # order: set expired -> bulk download

    # Extract stops from Naptan.xml
    naptan_file_path = get_latest_naptan_xml()

    # Extract NPTG.xml
    nptg_file_path = get_latest_nptg()

    # Extract stops
    stops_naptan = extract_stops(naptan_file_path)

    # Extract admin_areas
    admin_areas_naptan = extract_admin_areas(nptg_file_path)

    # Extract districts
    # districts_naptan = extract_districts(nptg_file_path)

    # Extract localities
    localities_naptan = extract_localities(nptg_file_path)

    # Extract all data from DB
    stops_from_db = extract_stops_from_db()
    admin_areas_from_db = extract_admin_areas_from_db()
    extract_districts_from_db()
    localities_from_db = extract_localities_from_db()

    # Transform
    new_stops = get_new_data(stops_naptan, stops_from_db)
    existing_stops = get_existing_data(stops_naptan, stops_from_db, "atco_code")

    new_admin_areas = get_new_data(admin_areas_naptan, admin_areas_from_db)
    existing_admin_areas = get_existing_data(
        admin_areas_naptan, admin_areas_from_db, "id"
    )

    # new_districts = get_new_data(districts_naptan, districts_from_db)
    # existing_districts = get_existing_data(districts_naptan, districts_from_db, "id")

    new_localities = get_new_data(localities_naptan, localities_from_db)
    existing_localities = get_existing_data(
        localities_naptan, localities_from_db, "gazetteer_id"
    )

    # Load
    # logger.info(f"[naptan_etl: run]: New districts {len(new_districts)} found")
    # load_new_districts(new_districts)
    # load_existing_districts(existing_districts)

    logger.info(f"[naptan_etl: run]: New admin_areas {len(new_admin_areas)} found")
    load_new_admin_areas(new_admin_areas)
    load_existing_admin_areas(existing_admin_areas)

    logger.info(f"[naptan_etl: run]: New localities {len(new_localities)} found")
    load_new_localities(new_localities)
    load_existing_localities(existing_localities)

    logger.info(f"[naptan_etl: run]: New stops {len(new_stops)} found")
    load_new_stops(new_stops)
    load_existing_stops(existing_stops)

    # remove all the files on disk
    # TODO move these to the extract step, so clean the files once they are resolved
    # into dataframes

    cleanup()

    logger.info("[run] finished")
