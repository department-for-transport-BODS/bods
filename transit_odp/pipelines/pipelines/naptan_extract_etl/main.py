from transit_odp.pipelines.pipelines.naptan_extract_etl.lambda_handler import handler
from transit_odp.pipelines.pipelines.naptan_extract_etl.extract import (
    get_latest_naptan_to_s3,
)
from transit_odp.pipelines.pipelines.nptg_extract_etl.extract import (
    get_latest_nptg_to_s3,
)
from celery.utils.log import get_task_logger
from transit_odp.common.loggers import LoaderAdapter


logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)


def run():
    logger.info("Running NaPTAN API extract pipeline.")

    naptan_key = get_latest_naptan_to_s3()
    logger.info(f"Archived NaPTAN data to S3: {naptan_key}")

    nptg_key = get_latest_nptg_to_s3()
    logger.info(f"Archived NPTG data to S3: {nptg_key}")

    logger.info("[run] finished")
