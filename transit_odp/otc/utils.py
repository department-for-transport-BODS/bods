import pandas as pd
import csv
import logging
from io import StringIO
from typing import List, Optional

import botocore
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from waffle import flag_is_active

from transit_odp.browse.common import get_in_scope_in_season_lta_service_numbers
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.utils.s3_bucket_connection import get_s3_bodds_bucket_storage
from transit_odp.organisation.constants import SCOTLAND_TRAVELINE_REGIONS
from transit_odp.otc.models import LocalAuthority as OTCLocalAuthority
from transit_odp.otc.models import Service, UILta
from transit_odp.publish.requires_attention import (
    get_avl_records_require_attention_lta_line_level_objects,
    get_fares_records_require_attention_lta_line_level_objects,
    get_requires_attention_data_lta_line_level_objects,
)

logger = logging.getLogger(__name__)


def read_local_authority_comparison_file_from_s3_bucket():
    """
    Function that handles S3 bucket conenction to retrieve and read
    the local authority CSV file and extracts the necessary columns
    needed for the task.
    """
    try:
        logger.info("Connecting to S3 bucket.")

        csv_data = []
        bucket_name = getattr(settings, "AWS_BODDS_XSD_SCHEMA_BUCKET_NAME", None)
        csv_file_name = getattr(settings, "LOCAL_AUTHORITY_COMPARISON_FILE_NAME", None)
        storage = get_s3_bodds_bucket_storage()

        logger.info(f"Retrieving '{csv_file_name}' from S3 bucket.")
        storage.connection.meta.client.head_object(
            Bucket=bucket_name, Key=csv_file_name
        )

        file = storage._open(csv_file_name)
        content = file.read().decode()
        file.close()

        # Remove BOM character if present
        if content.startswith("\ufeff"):
            content = content.lstrip("\ufeff")

        csv_file = StringIO(content)
        reader = csv.DictReader(csv_file)
        for row in reader:
            csv_row = {
                "OTC name": row["OTC name"],
                "UI name": row["UI name"].replace("\xa0", " ").strip(),
                "Admin area": int(row["Admin area"]),
            }
            csv_data.append(csv_row)

        if csv_data:
            logger.info(f"Successfully read {len(csv_data)} LTAs from {csv_file_name}.")
        else:
            logger.warning(
                f"Issue in reading {csv_file_name} from S3 bucket - file may be empty."
            )

        return csv_data
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "403":
            logger.error(
                f"Permission denied (403) when accessing the S3 bucket: {bucket_name}"
            )
            return HttpResponse(
                "Permission denied when accessing the S3 bucket", status=403
            )
        else:
            logger.error(
                f"Error (Code: {error_code}) connecting to S3 bucket {bucket_name}: {str(e)}"
            )
            raise
    except Exception as e:
        logger.error(f"Error reading {csv_file_name} from S3: {str(e)}")
        raise


def get_ui_lta(ui_lta_name: str) -> Optional[UILta]:
    """
    Function to match and retrieve the 'name' of the LTA from the ui_lta table.

    Args:
        ui_lta_name (str): UI LTA name from CSV file

    Returns:
        UILta object or None
    """
    try:
        return UILta.objects.get(name=ui_lta_name)
    except UILta.DoesNotExist:
        logger.error(f"No UI LTA found with the name: '{ui_lta_name}'")


def check_missing_csv_lta_names(csv_data: List[dict]) -> set:
    """
    Function that compares which LTAs are present in the otc_localauthority
    table but are not in the CSV 'OTC name' column.

    Args:
        csv_data (List[dict]): Data from the local authority CSV file

    Returns:
        set: Includes list of missing CSV lta names
    """
    csv_lta_names = set(lta_dict["OTC name"] for lta_dict in csv_data)
    missing_csv_lta_names = set()

    try:
        otc_db_names = OTCLocalAuthority.objects.values_list("name", flat=True)
    except Exception as e:
        logger.error("Failed to retrieve OTC names from database:", e)

    for otc_name in otc_db_names:
        if otc_name not in csv_lta_names:
            missing_csv_lta_names.add(otc_name)

    return missing_csv_lta_names


def is_service_in_scotland(service_ref: str) -> bool:
    service_name_in_cache = f"{service_ref.replace(':', '-')}-scottish-region"
    value_in_cache = cache.get(service_name_in_cache, None)

    if value_in_cache is not None:
        logger.info(f"{service_ref} PTI validation For region found in cache")
        return value_in_cache

    return get_service_in_scotland_from_db(service_ref)


def get_service_in_scotland_from_db(service_ref: str) -> bool:
    """Check weather a service is from the scotland region or not
    If any of the english regions is present service will be considered as english
    If only scottish is present then service will be considered as scottish

    Args:
        service_ref (str): service registration number

    Returns:
        bool: True/False if service is in scotland
    """
    logger.info(f"{service_ref} PTI validation For region checking in database")
    service_obj = (
        Service.objects.filter(registration_number=service_ref.replace(":", "/"))
        .add_traveline_region_weca()
        .add_traveline_region_otc()
        .add_traveline_region_details()
        .first()
    )
    is_scottish = False
    if service_obj and service_obj.traveline_region:
        regions = service_obj.traveline_region.split("|")
        if sorted(SCOTLAND_TRAVELINE_REGIONS) == sorted(regions):
            is_scottish = True

    service_name_in_cache = f"{service_ref.replace(':', '-')}-scottish-region"
    cache.set(service_name_in_cache, is_scottish, timeout=7200)
    return is_scottish


def uilta_calcualte_sra(
    uilta: UILta, uncounted_activity_df: pd.DataFrame, synced_in_last_month: List
):
    """SRA calculation for single UI LTA

    Args:
        organisation (Organisation): Organisation object
        uncounted_activity_df (pd.DataFrame): vehicle activity value
        synced_in_last_month (List): Abods lines list
    """
    try:
        is_avl_require_attention_active = flag_is_active(
            "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
        )

        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )

        lta_objs = uilta.localauthority_ui_lta_records.all()

        logger.debug(
            "UILTA Calculate SRA: Total {} Local Authority Objects Found".format(
                len(lta_objs)
            )
        )

        if lta_objs.count() <= 0:
            logger.debug(
                "Skipping SRA for UILTA {} with Zero Local Authorities".format(
                    uilta.name
                )
            )
            return

        avl_sra = fares_sra = []
        in_scope_services = get_in_scope_in_season_lta_service_numbers(lta_objs)
        timetable_sra = get_requires_attention_data_lta_line_level_objects(lta_objs)

        if is_avl_require_attention_active:
            avl_sra = get_avl_records_require_attention_lta_line_level_objects(
                lta_objs, uncounted_activity_df, synced_in_last_month
            )

        if is_fares_require_attention_active:
            fares_sra = get_fares_records_require_attention_lta_line_level_objects(
                lta_objs
            )

        overall_sra = get_overall_sra_unique_services(timetable_sra, avl_sra, fares_sra)
        uilta.total_inscope = len(in_scope_services)
        uilta.timetable_sra = len(timetable_sra)
        uilta.avl_sra = len(avl_sra)
        uilta.fares_sra = len(fares_sra)
        uilta.overall_sra = len(overall_sra)
        uilta.save()
    except Exception as e:
        logger.error(f"Error occured while syncing sra for uilta {uilta.name}")
        logger.exception(e)


def get_overall_sra_unique_services(
    timetable_sra: list, avl_sra: list, fares_sra: list
) -> List:
    all_sra = timetable_sra + avl_sra + fares_sra
    overall_sra = set()
    for d in all_sra:
        key = (
            d.get("licence_number")
            + "__"
            + d.get("service_code")
            + "__"
            + d.get("line_number")
        )
        overall_sra.add(key)
    return overall_sra
