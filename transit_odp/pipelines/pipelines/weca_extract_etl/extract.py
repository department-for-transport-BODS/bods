import json
import os
import hashlib
import datetime
from tempfile import mkstemp
from typing import TypedDict
from pathlib import Path

from django.conf import settings
from django.core.files.storage import Storage, default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from celery.utils.log import get_task_logger

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.pipelines.pipelines.weca_extract_etl.client import (
    APIServiceResponse,
    WecaClient,
    APIRegistrationsResponse,
)

logger = get_task_logger(__name__)
logger = LoaderAdapter("WECAIngest", logger)


class MetaData(TypedDict):
    """Metadata about the WECA data source, size, and validation count."""

    source: str
    size_mb: float
    validation_count: int
    checksum_sha256: str
    timestamp: str


def get_s3_storage() -> Storage:
    """Get storage for WECA data, preferring S3 if bucket name is configured
    otherwise falling back to default storage.

    Returns:
        Storage: Django Storage instance for WECA data
    """

    bucket_name = getattr(settings, "AWS_WECA_RAW_STORAGE_BUCKET_NAME", None) or os.getenv(
        "AWS_WECA_RAW_STORAGE_BUCKET_NAME"
    )

    if bucket_name:
        logger.info(f"Using S3 bucket for WECA data storage.")
        return S3Boto3Storage(bucket_name=bucket_name)
    else:
        logger.warning("WECA raw data storage location is not set. Using default storage.")
        return default_storage


def store_s3_data(
    response: APIServiceResponse | APIRegistrationsResponse, storage: Storage, key: str, client_url: str, checksum: str
) -> dict[str, MetaData]:
    """Store JSON data in S3.

    Args:
        response (APIServiceResponse | APIRegistrationsResponse): WECA Data model.
        storage (Storage): Django S3 Storage.
        key (str): S3 key to store the data under.
        client_url (str): WECA Client URL for metadata.
        checksum (str): File checksum for metadata.

    Returns:
        dict[str, MetaData]: File metadata.
    """

    try:
        # Ensure the default storage location exists if not using S3
        if not isinstance(storage, S3Boto3Storage):
            Path(os.path.join(storage.location, os.path.dirname(key))).mkdir(parents=True, exist_ok=True)

        with storage.open(key, "w") as f:
            data = response.model_dump_json()
            f.write(data)
            file_size_mb = len(data) / (1024 * 1024)

        metadata: MetaData = {
            "source": client_url,
            "size_mb": round(file_size_mb, 2),
            "validation_count": len(response.data),
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "checksum_sha256": checksum,
        }
        return {key: metadata}

    except Exception as e:
        logger.error("Exception while uploading WECA data to S3.", exc_info=e)
        raise


def store_temp_data(response: APIServiceResponse | APIRegistrationsResponse, prefix: str) -> str:
    """Write WECA data to a temporary file for comparison with previous data.

    Args:
        response (APIServiceResponse | APIRegistrationsResponse): The WECA data to write to a temp file.
        prefix (str): A prefix to use for the temp file name, e.g. "services" or "registrations".

    Returns:
        str: The path to the temp file that was created.
    """

    try:
        fd, temp_path = mkstemp(prefix=f"weca_{prefix}_", suffix=".json")
        with os.fdopen(fd, "w") as f:
            f.write(response.model_dump_json())
        return temp_path
    except Exception as e:
        logger.error("Exception while writing WECA data to temp file.", exc_info=e)
        raise


def get_metadata(storage: Storage, key: str) -> dict[str, MetaData]:
    """Fetch the previous WECA metadata from S3.

    Returns:
        dict[str, MetaData]: Previous WECA metadata as a dictionary with metadata about the source, size, and validation count.
    """

    try:
        if storage.exists(key):
            return json.loads(storage.open(key, "r").read())
        else:
            logger.warning(f"No previous WECA metadata found. Returning empty metadata.")
            return {}
    except Exception as e:
        logger.error("Exception while fetching previous WECA metadata from S3.", exc_info=e)
        raise


def create_sha256_checksum(temp_file_path: str) -> str:
    """Get a SHA256 checksum for a file.

    Args:
        temp_file_path (str): File path to the file to create a checksum for.

    Returns:
        str: The SHA256 checksum for the file.
    """

    sha256_hash = hashlib.sha256()
    with open(temp_file_path, "rb") as f:
        for bytes in iter(lambda: f.read(4096), b""):
            sha256_hash.update(bytes)
    return sha256_hash.hexdigest()


def has_changed(
    response: APIServiceResponse | APIRegistrationsResponse, previous_metadata: dict[str, str | MetaData], key: str
) -> tuple[bool, str]:
    # Write to temp & get checksums
    temp_file_path = store_temp_data(response, "data")
    checksum = create_sha256_checksum(temp_file_path)

    # Compare with previous version and upload if changed
    if previous_metadata.get(key) is None:
        logger.info(f"No previous metadata for {key}. Treating as new data.")
        return True, checksum
    elif previous_metadata[key].get("checksum_sha256") == checksum:
        return False, previous_metadata[key]["checksum_sha256"]

    return True, checksum


def validate_and_store(
    response: APIServiceResponse | APIRegistrationsResponse,
    previous_metadata: dict[str, str | MetaData],
    key: str,
    storage: Storage,
    client_url: str,
) -> dict[str, MetaData]:

    changed, checksum = has_changed(response, previous_metadata, key)
    if changed is False:
        logger.info(
            f"No changes detected in WECA data since {previous_metadata[key]['timestamp']}. Skipping S3 upload."
        )
        metadata = {key: previous_metadata[key]}
    else:
        metadata = store_s3_data(response, storage, key, client_url, checksum)

    return metadata


def get_latest_data() -> dict[str, str | MetaData]:
    """Fetch the latest WECA OTC data from WECA API, and store in S3.

    Returns:
        dict[str, MetaData]: Latest WECA data as a dictionary with metadata about the source, size, and validation count.
    """

    client = WecaClient()
    storage = get_s3_storage()
    metadata_key = os.getenv("WECA_S3_KEY_METADATA", "raw/weca/weca_metadata_latest.json")
    services_key = os.getenv("WECA_S3_KEY_SERVICES", "raw/weca/weca_services_latest.json")
    registrations_key = os.getenv("WECA_S3_KEY_REGISTRATIONS", "raw/weca/weca_registrations_latest.json")

    # Get the latest services and registrations data
    try:
        services = client.fetch_weca_services()
    except Exception as e:
        logger.error(f"Unable to fetch WECA Services data from {client.url}.", exc_info=e)
        raise

    try:
        registrations = client.fetch_weca_registrations()
    except Exception as e:
        logger.error(f"Unable to fetch WECA Registrations data from {client.url}.", exc_info=e)
        raise

    previous_metadata = get_metadata(storage, metadata_key)

    # Compare with previous version and upload if changed
    services_data = validate_and_store(services, previous_metadata, services_key, storage, client.url)
    registrations_data = validate_and_store(registrations, previous_metadata, registrations_key, storage, client.url)

    # Update metadata in S3
    weca_metadata = (
        {"last_checked": datetime.datetime.now(datetime.UTC).isoformat()} | services_data | registrations_data
    )
    with storage.open(metadata_key, "w") as f:
        data = json.dumps(weca_metadata, indent=4)
        f.write(data)

    return weca_metadata
