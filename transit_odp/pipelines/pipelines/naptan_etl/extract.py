import os
import shutil
from pathlib import Path

import pandas as pd
import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from lxml import etree as ET
from requests import RequestException

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.naptan.dataclasses import StopPoint
from transit_odp.naptan.dataclasses.nptg import NationalPublicTransportGazetteer

ns = "http://www.naptan.org.uk/"
namespace = {"naptan": ns}

CHUNK_SIZE = 8 * 1024 * 1024

DISK_PATH_FOR_NAPTAN_ZIP = "/tmp/NaptanStops.zip"

DISK_PATH_FOR_NAPTAN_FOLDER = "/tmp/NaptanStops/"
DISK_PATH_FOR_NPTG_FOLDER = "/tmp/NPTG/"
DISK_PATH_FOR_NPTG = "/tmp/NPTG.xml"

logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)


def get_latest_naptan_xml():
    naptan_url = settings.NAPTAN_IMPORT_URL
    logger.info(f"Loading NaPTAN file from {naptan_url}.")
    xml_file_path = None

    try:
        response = requests.get(naptan_url)
    except RequestException as exc:
        logger.error(f"Unable to fetch NaPTAN data from {naptan_url}.", exc_info=exc)
        return xml_file_path

    try:
        logger.info("Writing NaPTAN response data to a file on disk.")
        if response.status_code == 200:
            dir_path = Path(DISK_PATH_FOR_NAPTAN_FOLDER)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)

            filepath = dir_path / "Naptan.xml"
            with filepath.open("wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    f.write(chunk)

            logger.info("Finished NaPTAN writing to file on disk.")
            for filename in os.listdir(DISK_PATH_FOR_NAPTAN_FOLDER):
                if filename.endswith(".xml"):
                    xml_file_path = os.path.join(DISK_PATH_FOR_NAPTAN_FOLDER, filename)
    except Exception as exc:
        logger.error("Exception while getting NaPTAN data.", exc_info=exc)

    logger.info("NaPTAN file successfully extracted to disk.")
    return xml_file_path


def get_latest_nptg():
    nptg_url = settings.NPTG_IMPORT_URL
    logger.info(f"Loading NPTG from {nptg_url}.")
    xml_file_path = None
    try:
        response = requests.get(nptg_url)
        logger.info("Writing NPTG response data to a file on disk.")
        if response.status_code == 200:
            with open(DISK_PATH_FOR_NPTG, "wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    f.write(chunk)
            logger.info("Finished NPTG writing to file on disk.")
            xml_file_path = DISK_PATH_FOR_NPTG

    except Exception as e:
        logger.warning("Exception while getting NPTG data.", exc_info=e)

    logger.info("NPTG file successfully extracted to disk.")
    return xml_file_path


def extract_stops(xml_file_path):
    def inner():
        logger.info(f"Extracting NaPTAN stops from file {xml_file_path}.")
        tree = ET.parse(xml_file_path)

        stop_point_path = "//naptan:StopPoints/naptan:StopPoint"
        for stop in tree.iterfind(stop_point_path, namespaces=namespace):
            point = StopPoint.from_xml(stop)
            bus_stop_type, flexible_zones = None, None
            if (
                point.stop_classification.on_street
                and point.stop_classification.on_street.bus
            ):
                bus_stop_type = point.stop_classification.on_street.bus.bus_stop_type
                flexible_zones = point.stop_classification.on_street.bus.flexible_zones
            yield {
                "atco_code": point.atco_code,
                "naptan_code": point.naptan_code,
                "common_name": point.descriptor.common_name,
                "indicator": point.descriptor.indicator,
                "street": point.descriptor.street,
                "locality_id": point.place.nptg_locality_ref,
                "admin_area_id": int(point.administrative_area_ref),
                "latitude": point.place.location.translation.latitude,
                "longitude": point.place.location.translation.longitude,
                "stop_areas": point.stop_areas,
                "stop_type": point.stop_classification.stop_type,
                "bus_stop_type": bus_stop_type,
                "flexible_zones": flexible_zones,
            }

    df = pd.DataFrame(
        inner(),
        columns=[
            "atco_code",
            "naptan_code",
            "common_name",
            "indicator",
            "street",
            "locality_id",
            "admin_area_id",
            "latitude",
            "longitude",
            "stop_areas",
            "stop_type",
            "bus_stop_type",
            "flexible_zones",
        ],
    )
    logger.info(f"A total of {len(df)} NaPTAN stops extracted.")
    duplicated = df["atco_code"].duplicated(keep="first")
    duplicates = df[duplicated]
    if not duplicates.empty:
        logger.warning(
            f"{duplicates.shape[0]} duplicate StopPoint atco codes found. "
            "Sample of dropped rows:\n{duplicates.head()} "
        )
        df = df[~duplicated]

    df = df.set_index("atco_code", verify_integrity=True)

    logger.info(f"After deduplication {len(df)} NaPTAN stops extracted.")
    return df


def extract_admin_areas(xml_file_path):
    def inner():
        logger.info(f"Extracting NPTG AdminAreas from {xml_file_path}.")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        nptg = NationalPublicTransportGazetteer.from_xml(root)

        for region in nptg.regions:
            region_code = region.region_code
            for area in region.administrative_areas:
                yield {
                    "id": int(area.administrative_area_code),
                    "name": area.name,
                    "traveline_region_id": region_code,
                    "atco_code": area.atco_area_code,
                }

    df = pd.DataFrame(
        inner(),
        columns=["id", "name", "traveline_region_id", "atco_code"],
    ).set_index("id", verify_integrity=True)

    logger.info(f"{len(df)} NPTG AdminAreas extracted.")
    return df


def extract_localities(xml_file_path):
    logger.info(f"Extracting NPTG Localities from {xml_file_path}.")

    def inner():
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        nptg = NationalPublicTransportGazetteer.from_xml(root)

        for locality in nptg.nptg_localities:
            yield {
                "gazetteer_id": locality.nptg_locality_code,
                "name": locality.descriptor.locality_name,
                "easting": locality.location.translation.easting,
                "northing": locality.location.translation.northing,
                "district_id": int(locality.nptg_district_ref),
                "admin_area_id": int(locality.administrative_area_ref),
            }

    df = pd.DataFrame(
        inner(),
        columns=[
            "gazetteer_id",
            "name",
            "easting",
            "northing",
            "district_id",
            "admin_area_id",
        ],
    ).set_index("gazetteer_id", verify_integrity=True)

    logger.info(f"{len(df)} NPTG Localities extracted.")
    return df


def cleanup():
    logger.info("Cleaning up files saved to disk.")
    if os.path.exists(DISK_PATH_FOR_NAPTAN_ZIP):
        logger.info(f"Removing {DISK_PATH_FOR_NAPTAN_ZIP}.")
        os.remove(DISK_PATH_FOR_NAPTAN_ZIP)
    if os.path.exists(DISK_PATH_FOR_NAPTAN_FOLDER):
        logger.info(f"Removing {DISK_PATH_FOR_NAPTAN_FOLDER}.")
        shutil.rmtree(DISK_PATH_FOR_NAPTAN_FOLDER)
    if os.path.exists(DISK_PATH_FOR_NPTG):
        logger.info(f"Removing {DISK_PATH_FOR_NPTG}.")
        os.remove(DISK_PATH_FOR_NPTG)
    if os.path.exists(DISK_PATH_FOR_NPTG_FOLDER):
        logger.info(f"Removing {DISK_PATH_FOR_NPTG_FOLDER}.")
        shutil.rmtree(DISK_PATH_FOR_NPTG_FOLDER)


def get_latest_naptan_to_s3():
    """
    Download the latest NaPTAN XML (streamed) and upload it to S3 at
    `raw/naptan/latest.xml`. If an object already exists at that key it will
    be copied to an archive key with a timestamp prefix.

    Returns the S3 key of the uploaded file (i.e. `raw/naptan/latest.xml`).
    """
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    from datetime import datetime

    naptan_url = settings.NAPTAN_IMPORT_URL
    # Use getattr with fallback to support both Django settings and env vars.
    # Local testing may have settings not fully loaded; env fallback ensures compatibility.
    bucket_name = getattr(settings, "AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME", None) or os.getenv(
        "AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME"
    )

    if not bucket_name:
        raise ValueError("AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME is not configured")

    logger.info(f"Downloading latest NaPTAN XML from {naptan_url} (streamed)")
    try:
        # Use getattr with True default to support all environments.
        # Local: Set NAPTAN_SSL_VERIFY=True with custom CA bundle mount (see .env.naptan-test).
        # Prod Lambda: Uses NAPTAN_SSL_VERIFY=True with AWS-provided CA bundle (no custom setup needed).
        ssl_verify = getattr(settings, "NAPTAN_SSL_VERIFY", True)
        response = requests.get(naptan_url, stream=True, timeout=(30, 600), verify=ssl_verify)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - network/credentials dependent
        logger.error("Failed to download NaPTAN XML", exc_info=exc)
        raise

    # Ensure folder exists
    dir_path = Path(DISK_PATH_FOR_NAPTAN_FOLDER)
    dir_path.mkdir(parents=True, exist_ok=True)
    filepath = dir_path / "Naptan.xml"

    logger.info(f"Writing streamed NaPTAN to {filepath}")
    with filepath.open("wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)

    s3_client = boto3.client("s3")
    latest_key = "raw/naptan/latest.xml"

    # If there is an existing latest object, archive it by copying
    try:
        head = s3_client.head_object(Bucket=bucket_name, Key=latest_key)
        if head:
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            archive_key = f"raw/naptan/archives/{ts}-latest.xml"
            logger.info(f"Archiving existing latest object to {archive_key}")
            s3_client.copy_object(
                Bucket=bucket_name,
                CopySource={"Bucket": bucket_name, "Key": latest_key},
                Key=archive_key,
            )
    except ClientError as e:
        # If not found (404) there is no existing latest object - ignore
        if e.response.get("Error", {}).get("Code") not in ("404", "NoSuchKey"):
            logger.warning("Error checking existing latest object", exc_info=e)

    # Upload new latest
    try:
        logger.info(f"Uploading new latest to s3://{bucket_name}/{latest_key}")
        s3_client.upload_file(str(filepath), bucket_name, latest_key)
    except (BotoCoreError, ClientError) as exc:  # pragma: no cover - network/credentials dependent
        logger.error("Failed to upload NaPTAN XML to S3", exc_info=exc)
        raise

    logger.info("Successfully uploaded NaPTAN latest to S3")
    return latest_key
