from transit_odp.pipelines.pipelines.noc_extract_etl.lambda_handler import handler
from transit_odp.pipelines.pipelines.noc_extract_etl.extract import (
    get_latest_noc_to_s3,
)
from celery.utils.log import get_task_logger
from transit_odp.common.loggers import LoaderAdapter


logger = get_task_logger(__name__)
logger = LoaderAdapter("NOCLoader", logger)


def run():
    logger.info("Running NOC API extract pipeline.")

    noc_key = get_latest_noc_to_s3()
    logger.info(f"Archived NOC data to S3: {noc_key}")

    logger.info("[run] finished")
