import os

import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.files.storage import default_storage
from requests.exceptions import RequestException
from storages.backends.s3boto3 import S3Boto3Storage

from transit_odp.common.loggers import LoaderAdapter

logger = get_task_logger(__name__)
logger = LoaderAdapter("NPTGLoader", logger)


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks
HTTP_CONNECT_TIMEOUT = int(
    getattr(
        settings,
        "NPTG_HTTP_CONNECT_TIMEOUT",
        os.getenv("NPTG_HTTP_CONNECT_TIMEOUT", 30),
    )
)
HTTP_READ_TIMEOUT = int(
    getattr(
        settings, "NPTG_HTTP_READ_TIMEOUT", os.getenv("NPTG_HTTP_READ_TIMEOUT", 600)
    )
)


def get_nptg_s3_storage():
    bucket_name = getattr(settings, "NPTG_BUCKET_NAME", None) or os.getenv(
        "NPTG_BUCKET_NAME"
    )
    if bucket_name:
        logger.info(f"Using S3 bucket {bucket_name} for NPTG data storage.")
        return S3Boto3Storage(bucket_name=bucket_name)

    logger.warning("NPTG bucket is not set. Using default storage.")
    return default_storage


def get_latest_nptg_to_s3():
    nptg_url = settings.NPTG_IMPORT_URL
    latest_key = getattr(settings, "NPTG_S3_KEY", None) or os.getenv(
        "NPTG_S3_KEY", "raw/nptg/nptg_latest.xml"
    )
    verify_ssl = getattr(
        settings, "NPTG_SSL_VERIFY", _env_bool("NPTG_SSL_VERIFY", True)
    )
    storage = get_nptg_s3_storage()

    try:
        logger.info(
            f"Loading NPTG file from {nptg_url} and saving to S3 at {latest_key}."
        )

        response = requests.get(
            nptg_url,
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
                    validation_count += chunk.count(b"<NptgLocality")

        file_size_mb = total_bytes / (1024 * 1024)
        logger.info(
            f"NPTG data uploaded to S3 at {latest_key} "
            f"(size: {file_size_mb:.2f} MB, validation_count: {validation_count})."
        )

        return {
            latest_key: {
                "source": nptg_url,
                "size_mb": round(file_size_mb, 2),
                "validation_count": validation_count,
            }
        }
    except RequestException as exc:
        logger.error(f"Unable to fetch NPTG data from {nptg_url}.", exc_info=exc)
        raise
    except Exception as exc:
        logger.error("Exception while uploading NPTG data to S3.", exc_info=exc)
        raise
