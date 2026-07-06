import datetime
import hashlib
import json
import os
from pathlib import Path
from tempfile import mkstemp
from typing import Any, List, Optional

import requests
from celery.utils.log import get_task_logger
from django.core.files.storage import Storage, default_storage
from pydantic import BaseModel, Field, ValidationError
from storages.backends.s3boto3 import S3Boto3Storage

from transit_odp.common.loggers import LoaderAdapter

BUCKET_REGION = os.getenv("BUCKET_REGION")
BANK_HOLIDAY_S3_KEY = os.getenv("BANK_HOLIDAY_S3_KEY")
BANK_HOLIDAY_API_URL = os.getenv("BANK_HOLIDAY_API_URL")

CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks
HTTP_CONNECT_TIMEOUT = int(os.getenv("BANK_HOLIDAYS_HTTP_CONNECT_TIMEOUT", 30))
HTTP_READ_TIMEOUT = int(os.getenv("BANK_HOLIDAYS_HTTP_READ_TIMEOUT", 600))

logger = get_task_logger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG").upper())
logger = LoaderAdapter("BankHolidaysLoader", logger)


class Event(BaseModel):
    title: str
    date: str
    notes: Optional[str] = ""
    bunting: bool


class Division(BaseModel):
    division: str
    events: List[Event]


class APIBankHolidays(BaseModel):
    england_and_wales: Division = Field(alias="england-and-wales")
    scotland: Division


class MetaData(BaseModel):
    """Metadata about the bank holidays data source, size, and validation count."""

    source: str
    size_mb: float
    validation_count: int
    checksum_sha256: str
    timestamp: str


def get_bank_holiday_s3_storage() -> Storage:
    """Get storage for bank holidays data, preferring S3 if bucket name is configured
    otherwise falling back to default storage.

    Returns:
        Storage: Django Storage instance for bank holidays data
    """

    bucket_name = os.getenv("BANK_HOLIDAYS_BUCKET_NAME")

    if bucket_name:
        logger.info("Using S3 bucket for bank holidays data storage.")
        return S3Boto3Storage(
            bucket_name=bucket_name,
            object_parameters={"ServerSideEncryption": "aws:kms"},
        )
    else:
        logger.warning(
            "Bank holidays raw data storage location is not set. Using default storage."
        )
        return default_storage


def store_s3_data(
    data: APIBankHolidays | Any,
    storage: Storage,
    key: str,
    url: str,
    checksum: str,
) -> dict[str, MetaData]:
    """Store JSON data in S3.

    Args:
        data (APIBankHolidays | Any): bank holidays Data model, validated or raw.
        storage (Storage): Django S3 Storage.
        key (str): S3 key to store the data under.
        url (str): bank holidays URL for metadata.
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

        with storage.open(key, "wb") as f:
            total_bytes = 0
            validation_count = 0
            for chunk in data.iter_content(CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)
                    validation_count += chunk.count(b"title")

        file_size_mb = total_bytes / (1024 * 1024)

        metadata: MetaData = {
            "source": url,
            "size_mb": round(file_size_mb, 2),
            "validation_count": validation_count,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "checksum_sha256": checksum,
        }
        return {key: metadata}

    except Exception as e:
        logger.error("Exception while uploading Bank Holidays data to S3.", exc_info=e)
        raise


def get_metadata(storage: Storage, key: str) -> dict[str, str | MetaData]:
    """Fetch the previous bank holidays metadata from S3.

    Returns:
        dict[str, str | MetaData]: Previous bank holidays metadata as a dictionary with metadata about the source, size, and validation count.
    """

    try:
        if storage.exists(key):
            return json.loads(storage.open(key, "r").read())
        else:
            logger.warning(
                "No previous bank holidays metadata found. Returning empty metadata."
            )
            return {}
    except Exception as e:
        logger.error(
            "Exception while fetching previous bank holidays metadata from S3.",
            exc_info=e,
        )
        raise


def store_temp_data(data: APIBankHolidays | Any, prefix: str) -> str:
    """Write bank holidays data to a temporary file.

    Args:
        data (APIBankHolidays | Any): Raw or validated bank holidays response data.
        prefix (str): Base name for dataset, raw or validated.

    Returns:
        str: Path to temp file.
    """

    try:
        fd, temp_path = mkstemp(prefix=prefix, suffix=".json")
        with os.fdopen(fd, "wb") as f:
            for chunk in data.iter_content(CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        return temp_path
    except Exception as e:
        logger.error(
            "Exception while writing bank holidays data to temp file.", exc_info=e
        )
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
    data: APIBankHolidays | Any,
    previous_metadata: Optional[MetaData],
    base_name: str,
) -> tuple[bool, str]:
    """Check if there are changes between incoming and previous data.

    Args:
        data (APIBankHolidays | Any): Raw or validated bank holidays response data.
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
    data: APIBankHolidays | Any,
    previous_metadata: Optional[MetaData],
    s3_key: str,
    storage: Storage,
    url: str,
) -> dict[str, MetaData]:
    """Check if bank holidays data has changed since last ingestion, and store new data in S3.

    Args:
        data (APIBankHolidays | Any): bank holidays API response data, raw or validated.
        previous_metadata (Optional[MetaData]): Metadata from the previous ingestion if available.
        s3_key (str): Target S3 key
        storage (Storage): Storage object.
        url (str): bank holidays API URL.

    Returns:
        dict[str, MetaData]: Metadata for the current S3 key.
    """

    base_name = Path(s3_key).name.replace(Path(s3_key).suffix, "")
    changed, checksum = has_changed(data, previous_metadata, base_name)
    if changed is False:
        logger.info(
            f"No changes detected in bank holidays data since {previous_metadata['timestamp']}. Skipping S3 upload."
        )
        metadata = {s3_key: previous_metadata}
    else:
        metadata = store_s3_data(data, storage, s3_key, url, checksum)
    return metadata


def get_latest_bank_holidays_to_s3():
    logger.info("Starting bank holiday data export")
    keys = {
        "metadata": os.getenv(
            "BANK_HOLIDAY_S3_KEY_METADATA",
            "raw/bank_holidays/bank_holidays_metadata_latest.json",
        ),
        "latest": os.getenv(
            "BANK_HOLIDAY_S3_KEY_LATEST", "raw/bank_holidays/bank holidays_latest.json"
        ),
        "latest_validated": os.getenv(
            "BANK_HOLIDAY_S3_KEY_LATEST_VALIDATED",
            "raw/bank_holidays/bank_holidays_validated_latest.json",
        ),
    }
    logger.debug(f"Using S3 keys: {json.dumps(keys, indent=4)}")
    storage = get_bank_holiday_s3_storage()

    # WECA Pipeline metadata
    previous_metadata = get_metadata(storage, keys["metadata"])
    logger.debug(
        f"Previous bank holidays metadata: {json.dumps(previous_metadata, indent=4)}"
    )
    new_metadata = {
        "last_checked": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    try:
        logger.info(
            f"Loading bank holidays file from {BANK_HOLIDAY_API_URL} and saving to S3 at {keys['latest']}."
        )

        response = requests.get(BANK_HOLIDAY_API_URL)
        response.raise_for_status()

        # _ = APIBankHolidays.model_validate(response.json())

        raw_metadata = validate_and_store(
            response,
            previous_metadata.get(keys["latest"]),
            keys["latest"],
            storage,
            BANK_HOLIDAY_API_URL,
        )
        new_metadata = new_metadata | raw_metadata

    except Exception as e:
        logger.error(
            f"Unable to fetch Bank Holidays data from {BANK_HOLIDAY_API_URL}.",
            exc_info=e,
        )
        new_metadata = (
            new_metadata
            | {keys["latest"]: previous_metadata.get(keys["latest"])}
            | {
                keys["latest_validated"]: previous_metadata.get(
                    keys["latest_validated"]
                )
            }
        )

    try:
        _ = APIBankHolidays.model_validate(response.json())
        validated_metadata = validate_and_store(
            response,
            previous_metadata.get(keys["latest_validated"]),
            keys["latest_validated"],
            storage,
            BANK_HOLIDAY_API_URL,
        )

        new_metadata = new_metadata | validated_metadata
    except ValidationError as e:
        for error in e.errors():
            logger.error(f"Bank holiday validation error - {error}")
        new_metadata = new_metadata | {
            keys["latest_validated"]: previous_metadata.get(keys["latest_validated"])
        }
    except Exception as e:
        logger.error(
            f"Unable to fetch Bank Holidays data from {BANK_HOLIDAY_API_URL}.",
            exc_info=e,
        )
        new_metadata = new_metadata | {
            keys["latest_validated"]: previous_metadata.get(keys["latest_validated"])
        }

    # Update metadata in S3
    with storage.open(keys["metadata"], "w") as f:
        data = json.dumps(new_metadata, indent=4)
        f.write(data)

    return new_metadata
