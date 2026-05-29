from celery.utils.log import get_task_logger

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.pipelines.pipelines.nptg_extract_etl.extract import (
    get_latest_nptg_to_s3,
)

logger = get_task_logger(__name__)
logger = LoaderAdapter("NPTGLoader", logger)


def run():
    logger.info("Running NPTG API extract pipeline.")

    nptg_key = get_latest_nptg_to_s3()
    logger.info(f"Archived NPTG data to S3: {nptg_key}")

    logger.info("[run] finished")
