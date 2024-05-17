import logging
import csv
from io import StringIO

from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.common.utils.aws_common import get_s3_bucket_storage


logger = logging.getLogger(__name__)


def get_etl_task_or_pipeline_exception(pk) -> DatasetETLTaskResult:
    try:
        task = DatasetETLTaskResult.objects.get(pk=pk)
    except DatasetETLTaskResult.DoesNotExist as exc:
        message = f"DatasetETLTaskResult {pk} does not exist."
        logger.exception(message, exc_info=True)
        raise PipelineException(message) from exc
    else:
        return task


def read_fares_validator_rerun_datasets_file_from_s3():
    try:
        storage = get_s3_bucket_storage()
        file_name = "rerun_fares_validator.csv"

        if not storage.exists(file_name):
            logger.warning(f"{file_name} does not exist in the S3 bucket.")
            return []

        file = storage._open(file_name)
        content = file.read().decode()
        file.close()

        # Remove BOM character if present
        if content.startswith("\ufeff"):
            content = content.lstrip("\ufeff")

        csv_file = StringIO(content)
        reader = csv.DictReader(csv_file)
        dataset_ids = [
            int(row["Dataset ID"]) for row in reader if row["Dataset ID"].strip()
        ]

        if dataset_ids:
            logger.info(
                f"Successfully read {len(dataset_ids)} dataset IDs from {file_name} in S3."
            )
        else:
            logger.warning(
                f"{file_name} in S3 is empty or does not contain valid dataset IDs."
            )

        return dataset_ids
    except Exception as e:
        logger.error(f"Error reading {file_name} from S3: {str(e)}")
        raise
