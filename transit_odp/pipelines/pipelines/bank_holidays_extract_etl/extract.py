import os
from typing import List, Optional

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
    """Get storage for WECA data, preferring S3 if bucket name is configured
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


def get_latest_bank_holidays_to_s3():
    latest_key = os.getenv(
        "BANK_HOLIDAYS_S3_KEY", "raw/bank_holidays/bank_holidays_latest.json"
    )
    storage = get_bank_holiday_s3_storage()
    try:
        logger.info(
            f"Loading bank holidays file from {BANK_HOLIDAY_API_URL} and saving to S3 at {latest_key}."
        )

        response = requests.get(BANK_HOLIDAY_API_URL)
        response.raise_for_status()
        _ = APIBankHolidays.model_validate(response.json())

        total_bytes = 0
        validation_count = 0
        with storage.open(latest_key, "wb") as dst:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:
                    dst.write(chunk)
                    total_bytes += len(chunk)
                    validation_count += chunk.count(b"title")

        file_size_mb = total_bytes / (1024 * 1024)
        logger.info(
            f"Bank holidays data uploaded to S3 at {latest_key} "
            f"(size: {file_size_mb:.2f} MB, validation_count: {validation_count})."
        )

        return {
            latest_key: {
                "source": BANK_HOLIDAY_API_URL,
                "size_mb": round(file_size_mb, 2),
                "validation_count": validation_count,
            }
        }
    except ValidationError as e:
        for error in e.errors():
            logger.error(f"Bank holiday validation error - {error}")
        raise
    except Exception as exc:
        logger.error("Exception while uploading NPTG data to S3.", exc_info=exc)
        raise
