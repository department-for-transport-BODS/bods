import json
import os
import hashlib
import datetime
from tempfile import mkstemp
from typing import TypedDict, Any, Optional, get_args
from pathlib import Path

from django.core.files.storage import Storage, default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from celery.utils.log import get_task_logger

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.pipelines.pipelines.weca_extract_etl.client import (
    WECA_DATASETS,
    APIServiceResponse,
    WecaClient,
    APIRegistrationsResponse,
)

logger = get_task_logger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "WARNING").upper())
logger = LoaderAdapter("WECA - Ingest", logger)


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

    bucket_name = os.getenv("AWS_WECA_RAW_STORAGE_BUCKET_NAME")

    if bucket_name:
        logger.info(f"Using S3 bucket for WECA data storage.")
        return S3Boto3Storage(
            bucket_name=bucket_name,
            object_parameters={"ServerSideEncryption": "aws:kms"},
        )
    else:
        logger.warning(
            "WECA raw data storage location is not set. Using default storage."
        )
        return default_storage


def store_s3_data(
    data: APIServiceResponse | APIRegistrationsResponse | Any,
    storage: Storage,
    key: str,
    client_url: str,
    checksum: str,
) -> dict[str, MetaData]:
    """Store JSON data in S3.

    Args:
        data (APIServiceResponse | APIRegistrationsResponse | Any): WECA Data model, validated or raw.
        storage (Storage): Django S3 Storage.
        key (str): S3 key to store the data under.
        client_url (str): WECA Client URL for metadata.
        checksum (str): File checksum for metadata.

    Returns:
        dict[str, MetaData]: New metadata for uploaded file.
    """

    try:
        # Ensure the default storage location exists if not using S3
        if not isinstance(storage, S3Boto3Storage):
            Path(os.path.join(storage.location, os.path.dirname(key))).mkdir(
                parents=True, exist_ok=True
            )

        with storage.open(key, "w") as f:
            if isinstance(data, (APIRegistrationsResponse, APIServiceResponse)):
                data_out = data.model_dump_json()
                validation_count = len(data.data)
            else:
                data_out = json.dumps(data)
                validation_count = len(data["data"])

            f.write(data_out)
            file_size_mb = len(data_out) / (1024 * 1024)

        metadata: MetaData = {
            "source": client_url,
            "size_mb": round(file_size_mb, 2),
            "validation_count": validation_count,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checksum_sha256": checksum,
        }
        return {key: metadata}

    except Exception as e:
        logger.error("Exception while uploading WECA data to S3.", exc_info=e)
        raise


def get_metadata(storage: Storage, key: str) -> dict[str, str | MetaData]:
    """Fetch the previous WECA metadata from S3.

    Returns:
        dict[str, str | MetaData]: Previous WECA metadata as a dictionary with metadata about the source, size, and validation count.
    """

    try:
        if storage.exists(key):
            return json.loads(storage.open(key, "r").read())
        else:
            logger.warning(
                f"No previous WECA metadata found. Returning empty metadata."
            )
            return {}
    except Exception as e:
        logger.error(
            "Exception while fetching previous WECA metadata from S3.", exc_info=e
        )
        raise


def store_temp_data(
    data: APIServiceResponse | APIRegistrationsResponse | Any, prefix: str
) -> str:
    """Write WECA data to a temporary file.

    Args:
        data (APIServiceResponse | APIRegistrationsResponse | Any): Raw or validated WECA response data.
        prefix (str): Base name for dataset, raw or validated.

    Returns:
        str: Path to temp file.
    """

    try:
        fd, temp_path = mkstemp(prefix=prefix, suffix=".json")
        with os.fdopen(fd, "w") as f:
            if isinstance(data, (APIRegistrationsResponse, APIServiceResponse)):
                f.write(data.model_dump_json())
            else:
                f.write(json.dumps(data))
        return temp_path
    except Exception as e:
        logger.error("Exception while writing WECA data to temp file.", exc_info=e)
        raise


def create_sha256_checksum(temp_file_path: str) -> str:
    """Generate a SHA256 checksum for a file.

    Args:
        temp_file_path (str): Path to temp file.

    Returns:
        str: SHA256 checksum for file.
    """

    sha256_hash = hashlib.sha256()
    with open(temp_file_path, "rb") as f:
        for bytes in iter(lambda: f.read(4096), b""):
            sha256_hash.update(bytes)
    return sha256_hash.hexdigest()


def has_changed(
    data: APIServiceResponse | APIRegistrationsResponse | Any,
    previous_metadata: Optional[MetaData],
    base_name: str,
) -> tuple[bool, str]:
    """Check if there are changes between incoming and previous data.

    Args:
        data (APIServiceResponse | APIRegistrationsResponse | Any): Raw or validated WECA response data.
        previous_metadata (Optional[MetaData]): Metadata from previous ingestion if available.
        base_name (str): Base name for dataset, raw or validated.

    Returns:
        tuple[bool, str]: Has data changed, and the checksum.
    """

    temp_file_path = store_temp_data(data, base_name)
    checksum = create_sha256_checksum(temp_file_path)
    Path(temp_file_path).unlink(missing_ok=True)  # Remove temp file.

    if previous_metadata is None:
        logger.info(f"No previous metadata for {base_name}. Treating as new data.")
        return True, checksum
    elif previous_metadata.get("checksum_sha256") == checksum:
        return False, previous_metadata["checksum_sha256"]

    return True, checksum


def validate_and_store(
    data: APIServiceResponse | APIRegistrationsResponse | Any,
    previous_metadata: Optional[MetaData],
    s3_key: str,
    storage: Storage,
    client_url: str,
) -> dict[str, MetaData]:
    """Check if WECA data has changed since last ingestion, and store new data in S3.

    Args:
        data (APIServiceResponse | APIRegistrationsResponse | Any): WECA API response data, raw or validated.
        previous_metadata (Optional[MetaData]): Metadata from the previous ingestion if available.
        s3_key (str): Target S3 key
        storage (Storage): Storage object.
        client_url (str): WECA API URL.

    Returns:
        dict[str, MetaData]: Metadata for the current S3 key.
    """

    base_name = Path(s3_key).name.replace(Path(s3_key).suffix, "")
    changed, checksum = has_changed(data, previous_metadata, base_name)
    if changed is False:
        logger.info(
            f"No changes detected in WECA data since {previous_metadata['timestamp']}. Skipping S3 upload."
        )
        metadata = {s3_key: previous_metadata}
    else:
        metadata = store_s3_data(data, storage, s3_key, client_url, checksum)

    return metadata


def get_latest_data(
    services_params: Optional[dict[str, str]],
    registrations_params: Optional[dict[str, str]],
) -> dict[str, str | MetaData]:
    """Fetch the latest WECA data from WECA API, and store in S3.

    Args:
        services_params (Optional[dict[str, str]]): Params for WECA services requests.
        registrations_params (Optional[dict[str, str]]): Params for WECA registrations requests.

    Returns:
        dict[str, str | MetaData]: A dictionary with metadata covering the source, size, and validation count
    """

    # Get WECA client. There may not always be both types of request available.
    params = {"services": services_params, "registrations": registrations_params}
    if params.get("services"):
        url = params["services"]["url"]
    else:
        url = params["registrations"]["url"]
    client = WecaClient(url)

    # Get storage config
    storage = get_s3_storage()
    keys = {
        "metadata": os.getenv(
            "WECA_S3_KEY_METADATA", "raw/weca/weca_metadata_latest.json"
        ),
        "services": os.getenv(
            "WECA_S3_KEY_SERVICES", "raw/weca/weca_services_latest.json"
        ),
        "services_validated": os.getenv(
            "WECA_S3_KEY_SERVICES_VALID", "raw/weca/weca_services_validated_latest.json"
        ),
        "registrations": os.getenv(
            "WECA_S3_KEY_REGISTRATIONS", "raw/weca/weca_registrations_latest.json"
        ),
        "registrations_validated": os.getenv(
            "WECA_S3_KEY_REGISTRATIONS_VALID",
            "raw/weca/weca_registrations_validated_latest.json",
        ),
    }
    logger.debug(f"Using S3 keys: {json.dumps(keys, indent=4)}")

    # WECA Pipeline metadata
    previous_metadata = get_metadata(storage, keys["metadata"])
    logger.debug(f"Previous WECA metadata: {json.dumps(previous_metadata, indent=4)}")
    new_metadata = {
        "last_checked": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    # Get the latest services and registrations data
    for ds in get_args(WECA_DATASETS):

        ds_validated_key = keys[f"{ds}_validated"]

        try:
            # Skip if no params for this dataset
            if params.get(ds) is None:
                continue

            # Support for old and new format parameter secrets
            token = params[ds].get("api_key") or params[ds].get(f"api_key_{ds}")
            param_r = params[ds].get("param_r") or params[ds].get(f"param_r_{ds}")

            ds_raw = client.fetch_weca_data(
                ds,
                c_param=params[ds].get("param_c"),
                t_param=params[ds].get("param_t"),
                r_param=param_r,
                token=token,
            )
            ds_raw_metadata = validate_and_store(
                ds_raw, previous_metadata.get(keys[ds]), keys[ds], storage, client.url
            )
            new_metadata = new_metadata | ds_raw_metadata

        except Exception as e:
            logger.error(
                f"Unable to fetch WECA Services data from {client.url}.", exc_info=e
            )
            new_metadata = (
                new_metadata
                | {keys[ds]: previous_metadata.get(keys[ds])}
                | {ds_validated_key: previous_metadata.get(ds_validated_key)}
            )
            continue

        try:
            ds_validated = client.validate_weca_data(ds, ds_raw)
            ds_validated_metadata = validate_and_store(
                ds_validated,
                previous_metadata.get(ds_validated_key),
                ds_validated_key,
                storage,
                client.url,
            )

            new_metadata = new_metadata | ds_validated_metadata
        except Exception as e:
            logger.error(
                f"Unable to fetch WECA Services data from {client.url}.", exc_info=e
            )
            new_metadata = new_metadata | {
                ds_validated_key: previous_metadata.get(ds_validated_key)
            }
            continue

    # Update metadata in S3
    with storage.open(keys["metadata"], "w") as f:
        data = json.dumps(new_metadata, indent=4)
        f.write(data)

    return new_metadata
