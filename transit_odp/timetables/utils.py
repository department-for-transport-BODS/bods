import logging
import csv
from io import StringIO


from transit_odp.pipelines.constants import SchemaCategory
from transit_odp.pipelines.models import SchemaDefinition
from transit_odp.pipelines.pipelines.xml_schema import SchemaLoader
from transit_odp.timetables.constants import TXC_XSD_PATH
from django.conf import settings

from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger(__name__)


def get_transxchange_schema():
    definition = SchemaDefinition.objects.get(category=SchemaCategory.TXC)
    schema_loader = SchemaLoader(definition, TXC_XSD_PATH)
    return schema_loader.schema


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


def read_delete_datasets_file_from_s3():
    try:
        storage = get_s3_bucket_storage()
        file_name = "delete_datasets.csv"

        if not storage.exists(file_name):
            logger.warning(f"{file_name} does not exist in the S3 bucket.")
            return []

        file = storage._open(file_name)
        content = file.read().decode()
        file.close()
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
