from transit_odp.pipelines.pipelines.naptan_extract_etl.lambda_handler import handler
from transit_odp.pipelines.pipelines.naptan_extract_etl.extract import get_latest_naptan_to_s3
from celery.utils.log import get_task_logger
from transit_odp.common.loggers import LoaderAdapter


logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)

def run():
    logger.info("Running NaPTAN API extract pipeline.")

    naptan_key = get_latest_naptan_to_s3()
    logger.info(f"Archived NaPTAN data to S3: {naptan_key}")

    logger.info("[run] finished")