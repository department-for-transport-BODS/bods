import os
from typing import TypedDict

from django.conf import settings
from django.core.files.storage import Storage, default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from celery.utils.log import get_task_logger

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.pipelines.pipelines.weca_extract_etl.client import WecaClient

logger = get_task_logger(__name__)
logger = LoaderAdapter("WECAIngest", logger)


class MetaData(TypedDict):
    """Metadata about the WECA data source, size, and validation count."""

    source: str
    size_mb: float
    validation_count: int


def get_s3_storage() -> Storage:
    """Get storage for WECA data, preferring S3 if bucket name is configured
    otherwise falling back to default storage.

    Returns:
        Storage: Django Storage instance for WECA data
    """

    bucket_name = getattr(settings, "WECA_BUCKET_NAME", None) or os.getenv("WECA_BUCKET_NAME")

    if bucket_name:
        logger.info(f"Using S3 bucket for WECA data storage.")
        return S3Boto3Storage(bucket_name=bucket_name)
    else:
        logger.warning("WECA raw data storage location is not set. Using default storage.")
        return default_storage


def get_latest_data() -> dict[str, MetaData]:
    """Fetch the latest WECA OTC data from WECA API, and store in S3.

    Returns:
        dict[str, MetaData]: Latest WECA data as a dictionary with metadata about the source, size, and validation count.
    """

    try:
        client = WecaClient()
        response = client.fetch_weca_services()
    except Exception as e:
        logger.error(f"Unable to fetch WECA data from {client.url}.", exc_info=e)
        raise

    try:
        storage = get_s3_storage()
        latest_key = os.getenv("WECA_S3_KEY", "raw/weca/weca_latest.json")

        with storage.open(latest_key, "w") as f:
            data = response.model_dump_json()
            f.write(data)
            file_size_mb = len(data) / (1024 * 1024)

        metadata: MetaData = {
            "source": client.url,
            "size_mb": round(file_size_mb, 2),
            "validation_count": 1,
        }
        return {latest_key: metadata}

    except Exception as e:
        logger.error("Exception while uploading WECA data to S3.", exc_info=e)
        raise
