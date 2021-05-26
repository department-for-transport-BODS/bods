import os
import shutil
import zipfile

import pandas as pd
import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from lxml import etree as ET

logger = get_task_logger(__name__)

ns = "http://www.naptan.org.uk/"
namespace = {"naptan": ns}

CHUNK_SIZE = 2000

DISK_PATH_FOR_NAPTAN_ZIP = "/tmp/NaptanStops.zip"
DISK_PATH_FOR_NPTG_ZIP = "/tmp/NPTG.zip"

DISK_PATH_FOR_NAPTAN_FOLDER = "/tmp/NaptanStops/"
DISK_PATH_FOR_NPTG_FOLDER = "/tmp/NPTG/"


def get_latest_naptan_xml():
    logger.info("[get_latest_naptan_xml] called")
    xml_file_path = None
    try:
        naptan_url = settings.NAPTAN_IMPORT_URL
        response = requests.get(naptan_url)
        response.encoding = "utf-8"

        logger.info("Writing response data to a file on disk")
        if response.status_code == 200:
            with open(DISK_PATH_FOR_NAPTAN_ZIP, "wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    f.write(chunk)
            logger.info("Finished writing to file on disk")

            # Now that we have the zip file on disk, extract zip
            with zipfile.ZipFile(DISK_PATH_FOR_NAPTAN_ZIP, "r") as zip_ref:
                zip_ref.extractall(DISK_PATH_FOR_NAPTAN_FOLDER)

            for filename in os.listdir(DISK_PATH_FOR_NAPTAN_FOLDER):
                if filename.endswith(".xml"):
                    xml_file_path = os.path.join(DISK_PATH_FOR_NAPTAN_FOLDER, filename)
    except Exception:
        logger.info("Exception while getting Naptan data")
    logger.info("File extract done")
    return xml_file_path


def get_latest_nptg():
    logger.info("[get_latest_nptg] called")
    xml_file_path = None
    try:
        nptg_url = settings.NPTG_IMPORT_URL
        response = requests.get(nptg_url)
        logger.info("Writing response data to a file on disk")
        if response.status_code == 200:
            with open(DISK_PATH_FOR_NPTG_ZIP, "wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    f.write(chunk)
            logger.info("Finished writing to file on disk")

            # Now that we have the zip file on disk, extract zip
            with zipfile.ZipFile(DISK_PATH_FOR_NPTG_ZIP, "r") as zip_ref:
                zip_ref.extractall(DISK_PATH_FOR_NPTG_FOLDER)

            for filename in os.listdir(DISK_PATH_FOR_NPTG_FOLDER):
                if filename.endswith(".xml"):
                    xml_file_path = os.path.join(DISK_PATH_FOR_NPTG_FOLDER, filename)
    except Exception:
        logger.info("Exception while getting NPTG data")

    logger.info("File extract done")
    return xml_file_path


def extract_stops(xml_file_path):
    def inner():
        logger.info("[extract_stops] called")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for stop in root.iter(f"{{{ns}}}StopPoint"):
            yield {
                "atco_code": stop.findtext("naptan:AtcoCode", namespaces=namespace),
                "naptan_code": stop.findtext("naptan:NaptanCode", namespaces=namespace),
                "common_name": stop.findtext(
                    ".//naptan:CommonName", namespaces=namespace
                ),
                "indicator": stop.findtext(".//naptan:Indicator", namespaces=namespace),
                "street": stop.findtext(".//naptan:Street", namespaces=namespace),
                "locality_id": stop.findtext(
                    ".//naptan:NptgLocalityRef", namespaces=namespace
                ),
                "admin_area_id": int(
                    stop.findtext(
                        ".//naptan:AdministrativeAreaRef", namespaces=namespace
                    )
                ),
                "latitude": stop.findtext(".//naptan:Latitude", namespaces=namespace),
                "longitude": stop.findtext(".//naptan:Longitude", namespaces=namespace),
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

    duplicated = df["atco_code"].duplicated(keep="first")
    duplicates = df[duplicated]
    if not duplicates.empty:
        logger.warning(
            f"{duplicates.shape[0]} duplicate StopPoint atco codes found. "
            "Sample of dropped rows:\n{duplicates.head()} "
        )
        df = df[~duplicated]

    df = df.set_index("atco_code", verify_integrity=True)
    logger.info("[extract_stops] finished")
    return df


def extract_admin_areas(xml_file_path):
    def inner():
        logger.info("[extract_admin_areas] called")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for region in root.iter(f"{{{ns}}}Region"):
            for admin_area in region.iter(f"{{{ns}}}AdministrativeArea"):
                yield {
                    "id": int(
                        admin_area.findtext(
                            "naptan:AdministrativeAreaCode", namespaces=namespace
                        )
                    ),
                    "name": admin_area.findtext("naptan:Name", namespaces=namespace),
                    "traveline_region_id": region.findtext(
                        "naptan:RegionCode", namespaces=namespace
                    ),
                    "atco_code": admin_area.findtext(
                        "naptan:AtcoAreaCode", namespaces=namespace
                    ),
                }

    df = pd.DataFrame(
        inner(),
        columns=["id", "name", "traveline_region_id", "atco_code"],
    ).set_index("id", verify_integrity=True)
    logger.info("[extract_admin_areas] finished")
    return df


def extract_districts(xml_file_path):
    def inner():
        logger.info("[extract_districts] called")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for district in root.iter(f"{{{ns}}}NptgDistrict"):
            yield {
                "id": int(
                    district.findtext("naptan:NptgDistrictCode", namespaces=namespace)
                ),
                "name": district.findtext("naptan:Name", namespaces=namespace),
            }

    df = pd.DataFrame(
        inner(),
        columns=["id", "name"],
    ).set_index("id", verify_integrity=True)
    logger.info("[extract_localities] finished")
    return df


def extract_localities(xml_file_path):
    def inner():
        logger.info("[extract_localities] called")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for locality in root.iter(f"{{{ns}}}NptgLocality"):
            yield {
                "gazetteer_id": locality.findtext(
                    "naptan:NptgLocalityCode", namespaces=namespace
                ),
                "name": locality.findtext(
                    ".//naptan:LocalityName", namespaces=namespace
                ),
                "easting": int(
                    locality.findtext(".//naptan:Easting", namespaces=namespace)
                ),
                "northing": int(
                    locality.findtext(".//naptan:Northing", namespaces=namespace)
                ),
                "district_id": int(
                    locality.findtext("naptan:NptgDistrictRef", namespaces=namespace)
                ),
                "admin_area_id": int(
                    locality.findtext(
                        "naptan:AdministrativeAreaRef", namespaces=namespace
                    )
                ),
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

    logger.info("[extract_localities] finished")
    return df


def cleanup():
    if os.path.exists(DISK_PATH_FOR_NAPTAN_ZIP):
        os.remove(DISK_PATH_FOR_NAPTAN_ZIP)
    if os.path.exists(DISK_PATH_FOR_NAPTAN_FOLDER):
        shutil.rmtree(DISK_PATH_FOR_NAPTAN_FOLDER)
    if os.path.exists(DISK_PATH_FOR_NPTG_ZIP):
        os.remove(DISK_PATH_FOR_NPTG_ZIP)
    if os.path.exists(DISK_PATH_FOR_NPTG_FOLDER):
        shutil.rmtree(DISK_PATH_FOR_NPTG_FOLDER)
