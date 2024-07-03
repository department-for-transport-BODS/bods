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
        storage = get_s3_bucket_storage()

        if not storage.exists(csv_file_name):
            logger.warning(f"{csv_file_name} does not exist in the S3 bucket.")
            return [], None

        file = storage._open(csv_file_name)
        content = file.read().decode()
        file.close()

        # Remove BOM character if present
        if content.startswith("\ufeff"):
            content = content.lstrip("\ufeff")

        # Parse the CSV content
        csv_file = StringIO(content)
        reader = csv.DictReader(csv_file)

        _ids = []
        _id_type = ""
        _column_name = ""

        column_names = reader.fieldnames

        if column_names[0].lower() == "dataset id":
            _column_name = column_names[0]
            _id_type = "dataset_id"
        elif column_names[0].lower() == "dataset revision id":
            _column_name = column_names[0]
            _id_type = "dataset_revision_id"
        else:
            _column_name = ""
            _id_type = None

        if _column_name:
            _ids = [
                int(row[_column_name]) for row in reader if row[_column_name].strip()
            ]

        return _ids, _id_type

    except Exception as e:
        logger.error(f"Error reading {csv_file_name} from S3: {str(e)}")
        raise
