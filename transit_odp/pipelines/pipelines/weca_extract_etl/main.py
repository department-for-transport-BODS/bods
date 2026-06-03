import logging
from celery.utils.log import get_task_logger

from transit_odp.pipelines.pipelines.weca_extract_etl.extract import get_latest_data
from transit_odp.common.loggers import LoaderAdapter


logger = get_task_logger(__name__)
logger = LoaderAdapter("WECAIngest", logger)


def run():
    logger.info("Running WECA API extract pipeline.")

    weca_key = get_latest_data()
    logger.info(f"Archived WECA data to S3: {weca_key}")

    logger.info("[run] finished")


if __name__ == "__main__":
    run()
