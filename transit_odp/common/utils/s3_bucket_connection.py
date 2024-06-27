import csv
import logging
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


def get_s3_bodds_bucket_storage():
    """
    Function that retrieves the S3 bucket.
    """
    bucket_name = getattr(settings, "AWS_BODDS_XSD_SCHEMA_BUCKET_NAME", None)
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


def read_datasets_file_from_s3(csv_file_name: str) -> tuple:
    """Read csv from S3 bucket and return a list of dataset ids and dataset revision ids"""
    try:
        s3_client, bucket_name = get_s3_bucket_storage()

        # Check if the file exists in the S3 bucket
        try:
            s3_client.head_object(Bucket=bucket_name, Key=csv_file_name)
        except s3_client.exceptions.ClientError:
            logger.warning(f"{csv_file_name} does not exist in the S3 bucket.")
            return [], [], "none"

        # Read the file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=csv_file_name)
        content = response["Body"].read().decode()

        # Remove BOM character if present
        if content.startswith("\ufeff"):
            content = content.lstrip("\ufeff")

        # Parse the CSV content
        csv_file = StringIO(content)
        reader = csv.DictReader(csv_file)

        dataset_ids = []
        dataset_revision_ids = []
        for row in reader:
            if row.get("Dataset ID") and row["Dataset ID"].strip():
                dataset_ids.append(int(row["Dataset ID"]))
            if row.get("Dataset revision ID") and row["Dataset revision ID"].strip():
                dataset_revision_ids.append(int(row["Dataset revision ID"]))

        if dataset_ids:
            logger.info(
                f"Successfully read {len(dataset_ids)} dataset IDs from {csv_file_name} in S3."
            )
            return dataset_ids, dataset_revision_ids, "dataset_ids"
        elif dataset_revision_ids:
            logger.info(
                f"Successfully read {len(dataset_revision_ids)} dataset revision IDs from {csv_file_name} in S3."
            )
            return dataset_ids, dataset_revision_ids, "dataset_revision_ids"
        else:
            logger.warning(
                f"{csv_file_name} in S3 is empty or does not contain valid dataset IDs."
            )
            return [], [], "none"

    except Exception as e:
        logger.error(f"Error reading {csv_file_name} from S3: {str(e)}")
        raise
