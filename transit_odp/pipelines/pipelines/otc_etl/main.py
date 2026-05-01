from transit_odp.pipelines.pipelines.otc_etl.lambda_handler import handler
from transit_odp.pipelines.pipelines.otc_etl.extract import (
    get_latest_otc_to_s3,
)
from celery.utils.log import get_task_logger
from transit_odp.common.loggers import LoaderAdapter


logger = get_task_logger(__name__)
logger = LoaderAdapter("OTCLoader", logger)


def run():
    logger.info("Running OTC API extract pipeline.")

    otc_key = get_latest_otc_to_s3()
    logger.info(f"Archived OTC data to S3: {otc_key}")

    logger.info("[run] finished")