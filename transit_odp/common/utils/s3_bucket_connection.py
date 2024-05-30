import logging
import csv
from io import StringIO

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger(__name__)


def get_s3_bucket_storage():
    bucket_name = getattr(settings, "AWS_DATASET_MAINTENANCE_STORAGE_BUCKET_NAME", None)
    if not bucket_name:
        logger.error("Bucket name is not configured in settings.")
        raise ValueError("Bucket name is not configured in settings.")

    try:
        storage = S3Boto3Storage(bucket_name=bucket_name)
        logger.info(f"Successfully connected to S3 bucket: {bucket_name}")
        return storage
    except Exception as e:
        logger.error(f"Error connecting to S3 bucket {bucket_name}: {str(e)}")
        raise


def read_datasets_file_from_s3(csv_file_name: object) -> list:
    """Read csv from S3 bucket and return a list of dataset ids
    """
    try:
        storage = get_s3_bucket_storage()

        if not storage.exists(csv_file_name):
            logger.warning(f"{csv_file_name} does not exist in the S3 bucket.")
            return []

        file = storage._open(csv_file_name)
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
                f"Successfully read {len(dataset_ids)} dataset IDs from {csv_file_name} in S3."
            )
        else:
            logger.warning(
                f"{csv_file_name} in S3 is empty or does not contain valid dataset IDs."
            )

        return dataset_ids
    except Exception as e:
        logger.error(f"Error reading {csv_file_name} from S3: {str(e)}")
        raise
