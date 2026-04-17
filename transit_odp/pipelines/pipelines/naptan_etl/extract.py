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

from datetime import datetime
from io import BytesIO
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage

ns = "http://www.naptan.org.uk/"
namespace = {"naptan": ns}

CHUNK_SIZE = 2000

DISK_PATH_FOR_NAPTAN_ZIP = "/tmp/NaptanStops.zip"

DISK_PATH_FOR_NAPTAN_FOLDER = "/tmp/NaptanStops/"
DISK_PATH_FOR_NPTG_FOLDER = "/tmp/NPTG/"
DISK_PATH_FOR_NPTG = "/tmp/NPTG.xml"

logger = get_task_logger(__name__)
logger = LoaderAdapter("NaPTANLoader", logger)


def get_naptan_s3_storage():
    #Get S3 storage for NaPTAN data, or default storage if bucket name is not set
    bucket_name = getattr(settings, "AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME", None)
    if bucket_name:
        logger.info(f"Using S3 bucket {bucket_name} for NaPTAN data storage.")
        return S3Boto3Storage(bucket_name=bucket_name)
    else:
        logger.warning("AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME is not set. Using default storage.")
        return default_storage 


def archive_existing_s3_file(storage, current_key: str, data_type: str):
    # Move current latest file to an archive folder
    try:
        if storage.exists(current_key):
            #read the current file
            with storage.open(current_key, 'rb') as f:
                existing_data = f.read()

            try:
                obj = storage.bucket.Object(current_key)
                modified_time = obj.last_modified
                timestamp = modified_time.strftime("%Y-%m-%d_%H-%M-%S")
            except:
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            archive_key = f"raw/{data_type}/archive/{timestamp}.xml"

            archive_file = BytesIO(existing_data)
            storage.save(archive_key, archive_file)
            file_size_mb = len(existing_data) / (1024*1024)
            logger.info(f"Archived existing {data_type} file to S3 at {archive_key} (size: {file_size_mb:.2f} MB).")
        else:
            logger.info(f"No existing {data_type} file found in S3 at {current_key}")
    except Exception as exc:
        logger.warning(f"Error archiving existing {data_type} file in S3. Proceeding without archiving.", exc_info=exc)


def get_latest_naptan_to_s3():
    naptan_url = settings.NAPTAN_IMPORT_URL
    verify_ssl = getattr(settings, "NAPTAN_SSL_VERIFY", True)
    logger.info(f"Loading NaPTAN file from {naptan_url} and saving to S3.")

    try:
        response = requests.get(naptan_url, timeout=300, verify=verify_ssl)
        if response.status_code != 200:
            logger.error(f"Failed to fetch NaPTAN data from {naptan_url}. Status code: {response.status_code}")
            raise Exception(f"Failed to fetch NaPTAN data. Status code: {response.status_code}")
        
        raw_data = b""
        logger.info("Reading NaPTAN response data from S3")
        for chunk in response.iter_content(CHUNK_SIZE):
            raw_data += chunk

        storage = get_naptan_s3_storage()
        latest_key = f"raw/naptan/latest.xml"
        archive_existing_s3_file(storage, latest_key, "naptan")
        file_obj = BytesIO(raw_data)
        storage.save(latest_key, file_obj)
        file_size = len(raw_data) / (1024*1024)
        logger.info(f"NaPTAN data uploaded to S3 at {latest_key} (size: {file_size:.2f} MB).")

        return latest_key
    except RequestException as exc:
        logger.error(f"Unable to fetch NaPTAN data from {naptan_url}.", exc_info=exc)
        raise
    except Exception as exc:
        logger.error("Exception while uploading NaPTAN data to S3.", exc_info=exc)
        raise


def get_latest_naptan_xml():

    storage = get_naptan_s3_storage()
    s3_key = "raw/naptan/latest.xml"
    xml_file_path = None

    try:
        logger.info(f"Attempting to retrieve latest NaPTAN data from S3 at {s3_key}.")
        if not storage.exists(s3_key):
            logger.warning(f"No NaPTAN data found in S3 at {s3_key}")
            return None

        with storage.open(s3_key, "rb") as f:
            s3_data = f.read()
        
        filesize = len(s3_data) / (1024*1024)
        logger.info(f"Read NaPTAN data from S3 (size: {filesize:.2f} MB). Writing to disk for processing.")
        dir_path = Path(DISK_PATH_FOR_NAPTAN_FOLDER)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)

        filepath = dir_path / "Naptan.xml"
        with open(filepath, "wb") as f:
            f.write(s3_data)

        logger.info("Finished writing NaPTAN data to file on disk.")
        for filename in os.listdir(DISK_PATH_FOR_NAPTAN_FOLDER):
            if filename.endswith(".xml"):
                xml_file_path = os.path.join(DISK_PATH_FOR_NAPTAN_FOLDER, filename)

    except Exception as exc:
        logger.error("Exception while getting NaPTAN data.", exc_info=exc)

    logger.info("NaPTAN file successfully extracted to disk.")
    return xml_file_path


def upload_naptan_to_s3(data: bytes, data_type: str) -> str:
    # Uploads raw NaPTAN data to S3 & returns where it was saved
    storage = get_naptan_s3_storage()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    s3_key = f"raw/{data_type}/{timestamp}.xml" #Check this!

    file_obj = BytesIO(data)
    saved_path = storage.save(s3_key, file_obj)
    file_size = len(data) / (1024*1024)
    logger.info(f"Uploaded NaPTAN {data_type} data to S3 at {saved_path} (size: {file_size:.2f} MB).")
    return saved_path


def get_raw_data_from_s3(s3_key: str) -> bytes:
    # Gets raw data from S3 using the provided key
    storage = get_naptan_s3_storage()
    
    with storage.open(s3_key, 'rb') as f:
        data = f.read()
        
    file_size = len(data) / (1024*1024)
    logger.info(f"Downloaded data from S3 key {s3_key} (size: {file_size:.2f} MB).")
    return data


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
