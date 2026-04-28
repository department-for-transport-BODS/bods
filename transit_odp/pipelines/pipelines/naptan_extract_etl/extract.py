import os
import requests
from requests.exceptions import RequestException

from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from celery.utils.log import get_task_logger
from transit_odp.common.loggers import LoaderAdapter

logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)

CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks
HTTP_CONNECT_TIMEOUT = int(
    getattr(
        settings,
        "NAPTAN_HTTP_CONNECT_TIMEOUT",
        os.getenv("NAPTAN_HTTP_CONNECT_TIMEOUT", 30),
    )
)
HTTP_READ_TIMEOUT = int(
    getattr(
        settings, "NAPTAN_HTTP_READ_TIMEOUT", os.getenv("NAPTAN_HTTP_READ_TIMEOUT", 600)
    )
)

def get_naptan_s3_storage():
    # Get S3 storage for NaPTAN data, or default storage if bucket name is not set
    bucket_name = getattr(
        settings, "AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME", None
    ) or os.getenv("AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME")
    if bucket_name:
        logger.info(f"Using S3 bucket {bucket_name} for NaPTAN data storage.")
        return S3Boto3Storage(bucket_name=bucket_name)
    else:
        logger.warning(
            "AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME is not set. Using default storage."
        )
        return default_storage


def get_latest_naptan_to_s3():
    xml_url = settings.NAPTAN_XML_IMPORT_URL
    csv_url = settings.NAPTAN_CSV_IMPORT_URL
    verify_ssl = getattr(settings, "NAPTAN_SSL_VERIFY", True)
    storage = get_naptan_s3_storage()

    uploads = [
        (xml_url, "raw/naptan/naptan_latest_xml.xml"),
        (csv_url, "raw/naptan/naptan_latest_csv.csv"),
    ]
    uploaded_files = []

    for naptan_url, latest_key in uploads:
        logger.info(
            f"Loading NaPTAN file from {naptan_url} and saving to S3 at {latest_key}."
        )

        try:
            response = requests.get(
                naptan_url,
                timeout=(HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT),
                verify=verify_ssl,
                stream=True,
            )
            response.raise_for_status()

            total_bytes = 0
            with storage.open(latest_key, "wb") as dst:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:
                        dst.write(chunk)
                        total_bytes += len(chunk)

            file_size_mb = total_bytes / (1024 * 1024)
            logger.info(
                f"NaPTAN data uploaded to S3 at {latest_key} (size: {file_size_mb:.2f} MB)."
            )
            uploaded_files.append({latest_key: naptan_url})

        except RequestException as exc:
            logger.error(f"Unable to fetch NaPTAN data from {naptan_url}.", exc_info=exc)
            raise
        except Exception as exc:
            logger.error("Exception while uploading NaPTAN data to S3.", exc_info=exc)
            raise
    
    return uploaded_files