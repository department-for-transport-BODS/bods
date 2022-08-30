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

CHUNK_SIZE = 2000

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
