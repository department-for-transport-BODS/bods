import os
import re
import tempfile
import zipfile
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
    getattr(settings, "NOC_HTTP_READ_TIMEOUT", os.getenv("NOC_HTTP_READ_TIMEOUT", 600))
)
ZIP_ALLOWED_EXTENSIONS = [".zip"]
CSV_ALLOWED_EXTENSIONS = [".csv"]
NOC_CSV_TABLE_NAMES = {
    table_name.lower() for table_name in getattr(settings, "NOC_CSV_TABLE_NAMES", ())
}
NOC_CSV_TABLE_NAME_MAP = {
    table_name.removeprefix("table_"): table_name for table_name in NOC_CSV_TABLE_NAMES
}
NOC_CSV_TABLE_NAME_ALIASES = {
    "noc_lines": "table_noclines",
}


def _normalise_table_name(filename):
    basename = os.path.splitext(filename)[0]
    snake_case = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", basename)
    snake_case = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", snake_case).lower()
    return snake_case


def _download_to_temp_file(response):
    temp_file = tempfile.NamedTemporaryFile(mode="w+b", delete=False)
    temp_path = temp_file.name
    total_bytes = 0

    try:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                temp_file.write(chunk)
                total_bytes += len(chunk)
        temp_file.flush()
    finally:
        temp_file.close()

    return temp_path, total_bytes


def _upload_file_to_storage(storage, source_path, destination_key):
    with open(source_path, "rb") as src, storage.open(destination_key, "wb") as dst:
        for chunk in iter(lambda: src.read(CHUNK_SIZE), b""):
            if chunk:
                dst.write(chunk)


def _extract_and_upload_noc_csv(storage, zip_file_path, latest_key):
    extracted_keys = []
    destination_prefix = "raw/noc"

    with zipfile.ZipFile(zip_file_path, "r") as archive:
        csv_members = [
            member
            for member in archive.namelist()
            if not member.endswith("/")
            and os.path.splitext(member)[1].lower() in CSV_ALLOWED_EXTENSIONS
        ]

        if not csv_members:
            raise ValueError("NOC ZIP archive did not contain any CSV files.")

        for member in csv_members:
            filename = os.path.basename(member)
            if not filename:
                continue

            source_table_name = _normalise_table_name(filename)
            mapped_table_name = NOC_CSV_TABLE_NAME_MAP.get(source_table_name)

            if not mapped_table_name:
                mapped_table_name = NOC_CSV_TABLE_NAME_ALIASES.get(source_table_name)

            # Support direct matches where upstream already provides table_ prefixes.
            if not mapped_table_name and source_table_name in NOC_CSV_TABLE_NAMES:
                mapped_table_name = source_table_name

            if not mapped_table_name:
                logger.warning(
                    f"Skipping NOC archive member {filename}: no table mapping configured."
                )
                continue

            destination_key = f"{destination_prefix}/{mapped_table_name}_latest_csv.csv"
            with archive.open(member) as src, storage.open(
                destination_key, "wb"
            ) as dst:
                for chunk in iter(lambda: src.read(CHUNK_SIZE), b""):
                    if chunk:
                        dst.write(chunk)
            extracted_keys.append(destination_key)

    return extracted_keys


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
    xml_url = settings.NOC_XML_IMPORT_URL
    csv_url = settings.NOC_CSV_IMPORT_URL
    verify_ssl = getattr(settings, "NOC_SSL_VERIFY", True)
    storage = get_noc_s3_storage()

    uploads = [
        (xml_url, "raw/noc/noc_latest_xml.xml"),
        (csv_url, "raw/noc/noc_latest_csv.csv"),
    ]
    uploaded_files = []

    for noc_url, latest_key in uploads:
        logger.info(
            f"Loading NOC file from {noc_url} and saving to S3 at {latest_key}."
        )

        temp_file_path = None
        try:
            response = requests.get(
                noc_url,
                timeout=(HTTP_CONNECT_TIMEOUT, HTTP_READ_TIMEOUT),
                verify=verify_ssl,
                stream=True,
            )
            response.raise_for_status()

            temp_file_path, total_bytes = _download_to_temp_file(response)

            if latest_key.endswith(".csv") and zipfile.is_zipfile(temp_file_path):
                logger.info(
                    "Downloaded CSV payload as ZIP; "
                    f"accepted archive extensions {ZIP_ALLOWED_EXTENSIONS}, "
                    f"extracting files with extensions {CSV_ALLOWED_EXTENSIONS}."
                )
                uploaded_keys = _extract_and_upload_noc_csv(
                    storage, temp_file_path, latest_key
                )
                for uploaded_key in uploaded_keys:
                    uploaded_files.append({uploaded_key: noc_url})
            else:
                _upload_file_to_storage(storage, temp_file_path, latest_key)
                uploaded_files.append({latest_key: noc_url})

            file_size_mb = total_bytes / (1024 * 1024)
            logger.info(
                f"NOC data uploaded to S3 at {latest_key} (size: {file_size_mb:.2f} MB)."
            )

        except RequestException as exc:
            logger.error(f"Unable to fetch NOC data from {noc_url}.", exc_info=exc)
            raise
        except Exception as exc:
            logger.error("Exception while uploading NOC data to S3.", exc_info=exc)
            raise
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    return uploaded_files