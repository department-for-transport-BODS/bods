import os
import requests
from requests.exceptions import RequestException

from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from celery.utils.log import get_task_logger
from transit_odp.common.loggers import LoaderAdapter

logger = get_task_logger(__name__)
logger = LoaderAdapter("NOCLoader", logger)

CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks
HTTP_CONNECT_TIMEOUT = int(
    getattr(
        settings,
        "NOC_HTTP_CONNECT_TIMEOUT",
        os.getenv("NOC_HTTP_CONNECT_TIMEOUT", 30),
    )
)
HTTP_READ_TIMEOUT = int(
    getattr(
        settings, "NOC_HTTP_READ_TIMEOUT", os.getenv("NOC_HTTP_READ_TIMEOUT", 600)
    )
)

def get_noc_s3_storage():
    # Get S3 storage for NOC data, or default storage if bucket name is not set
    bucket_name = getattr(
        settings, "AWS_NOC_RAW_STORAGE_BUCKET_NAME", None
    ) or os.getenv("AWS_NOC_RAW_STORAGE_BUCKET_NAME")
    if bucket_name:
        logger.info(f"Using S3 bucket {bucket_name} for NOC data storage.")
        return S3Boto3Storage(bucket_name=bucket_name)
    else:
        logger.warning(
            "AWS_NOC_RAW_STORAGE_BUCKET_NAME is not set. Using default storage."
        )
        return default_storage


def get_latest_noc_to_s3():
    noc_url = settings.NOC_IMPORT_URL
    latest_key = "raw/noc/noc_latest.xml"
    verify_ssl = getattr(settings, "NOC_SSL_VERIFY", True)
    storage = get_noc_s3_storage()

    try:
        logger.info(
            f"Loading NOC file from {noc_url} and saving to S3 at {latest_key}."
        )

        response = requests.get(
            noc_url,
            timeout=(HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT),
            verify=verify_ssl,
            stream=True,
        )
        response.raise_for_status()

        total_bytes = 0
        validation_count = 0
        with storage.open(latest_key, "wb") as dst:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:
                    dst.write(chunk)
                    total_bytes += len(chunk)
                    validation_count += chunk.count(b"<NocEntry")

        file_size_mb = total_bytes / (1024 * 1024)
        logger.info(
            f"NOC data uploaded to S3 at {latest_key} "
            f"(size: {file_size_mb:.2f} MB, validation_count: {validation_count})."
        )

        return {
            latest_key: {
                "source": noc_url,
                "size_mb": round(file_size_mb, 2),
                "validation_count": validation_count,
            }
        }
    except RequestException as exc:
        logger.error(f"Unable to fetch NOC data from {noc_url}.", exc_info=exc)
        raise
    except Exception as exc:
        logger.error("Exception while uploading NOC data to S3.", exc_info=exc)
        raise
