import os
import shutil
from pathlib import Path
import io

import pandas as pd
import requests
from celery.utils.log import get_task_logger
from lxml import etree as ET
from requests import RequestException

from transit_odp.common.loggers import LoaderAdapter
from transit_odp.naptan.dataclasses import StopPoint
from transit_odp.naptan.dataclasses.nptg import NationalPublicTransportGazetteer

from storages.backends.s3boto3 import S3Boto3Storage

ns = "http://www.naptan.org.uk/"
namespace = {"naptan": ns}

CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks

NAPTAN_BUCKET_NAME = os.getenv("NAPTAN_BUCKET_NAME")
BUCKET_REGION = os.getenv("BUCKET_REGION")
NAPTAN_S3_KEY = os.getenv("NAPTAN_S3_KEY")
NPTG_BUCKET_NAME = os.getenv("NPTG_BUCKET_NAME")
NPTG_S3_KEY = os.getenv("NPTG_S3_KEY")

DISK_PATH_FOR_NAPTAN_ZIP = "/tmp/NaptanStops.zip"

DISK_PATH_FOR_NAPTAN_FOLDER = "/tmp/Naptan/"
DISK_PATH_FOR_NPTG_FOLDER = "/tmp/NPTG/"
DISK_PATH_FOR_NPTG = "/tmp/NPTG.xml"

logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)
nptg_logger = LoaderAdapter("NPTGLoader", get_task_logger(__name__))


def get_naptan_s3_storage():
    # NaPTAN reads must use the configured S3 bucket.
    if NAPTAN_BUCKET_NAME:
        logger.info(f"Using S3 bucket {NAPTAN_BUCKET_NAME} for NaPTAN data storage.")
        storage_kwargs = {"bucket_name": NAPTAN_BUCKET_NAME}
        if BUCKET_REGION:
            storage_kwargs["region_name"] = BUCKET_REGION
        return S3Boto3Storage(**storage_kwargs)

    message = "NAPTAN_BUCKET_NAME is not set. Cannot read NaPTAN data from S3."
    logger.error(message)
    raise RuntimeError(message)


def get_nptg_s3_storage():
    if not NPTG_BUCKET_NAME:
        message = "NPTG_BUCKET_NAME is not set. Cannot read NPTG data from S3."
        nptg_logger.error(message)
        raise RuntimeError(message)

    storage_kwargs = {"bucket_name": NPTG_BUCKET_NAME}
    if BUCKET_REGION:
        storage_kwargs["region_name"] = BUCKET_REGION

    nptg_logger.info(f"Using S3 bucket {NPTG_BUCKET_NAME} for NPTG data storage.")
    return S3Boto3Storage(**storage_kwargs)


def get_latest_naptan_xml():
    storage = get_naptan_s3_storage()
    s3_key = NAPTAN_S3_KEY
    if not s3_key:
        logger.error("NAPTAN_S3_KEY is not set.")
        return None

    try:
        logger.info(f"Attempting to retrieve latest NaPTAN data from S3 at {s3_key}.")
        if not storage.exists(s3_key):
            logger.warning(f"No NaPTAN data found in S3 at {s3_key}")
            return None

        logger.info(f"NaPTAN XML found in S3 at {s3_key}.")
        return storage.open(s3_key, "rb")

    except Exception as exc:
        logger.error("Exception while getting NaPTAN data.", exc_info=exc)
        return None


def get_latest_nptg():
    storage = get_nptg_s3_storage()
    s3_key = NPTG_S3_KEY
    if not s3_key:
        nptg_logger.warning("NPTG_S3_KEY is not set.")
        return None

    nptg_logger.info(f"Attempting to retrieve latest NPTG data from S3 at {s3_key}.")
    xml_file_path = None
    try:
        if not storage.exists(s3_key):
            nptg_logger.warning(f"No NPTG data found in S3 at {s3_key}")
            return None

        nptg_logger.info("Writing NPTG data from S3 to a file on disk.")
        with storage.open(s3_key, "rb") as source, open(DISK_PATH_FOR_NPTG, "wb") as f:
            for chunk in source.chunks(CHUNK_SIZE):
                f.write(chunk)

        nptg_logger.info("Finished NPTG writing to file on disk.")
        xml_file_path = DISK_PATH_FOR_NPTG

    except Exception as exc:
        nptg_logger.warning("Exception while getting NPTG data from S3.", exc_info=exc)

    nptg_logger.info("NPTG file successfully extracted to disk.")
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
    if os.path.exists(DISK_PATH_FOR_NPTG):
        logger.info(f"Removing {DISK_PATH_FOR_NPTG}.")
        os.remove(DISK_PATH_FOR_NPTG)
    if os.path.exists(DISK_PATH_FOR_NPTG_FOLDER):
        logger.info(f"Removing {DISK_PATH_FOR_NPTG_FOLDER}.")
        shutil.rmtree(DISK_PATH_FOR_NPTG_FOLDER)
