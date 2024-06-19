import csv
import logging
from io import StringIO
from typing import List, Optional

from transit_odp.common.utils.s3_bucket_connection import get_s3_bodds_bucket_storage
from transit_odp.otc.models import LocalAuthority as OTCLocalAuthority
from transit_odp.otc.models import UILta

logger = logging.getLogger(__name__)


def read_local_authority_comparison_file_from_s3_bucket():
    """
    Function that handles S3 bucket conenction to retrieve and read
    the local authority CSV file and extracts the necessary columns
    needed for the task.
    """
    try:
        logger.info("Connecting to S3 bucket and retrieving csv file")
        storage = get_s3_bodds_bucket_storage()
        csv_data = []
        file_name = "Local Authority Comparison (5).csv"

        if not storage.exists(file_name):
            logger.warning(f"{file_name} does not exist in the S3 bucket.")
            return []

        file = storage._open(file_name)
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
            logger.info(f"Successfully read {len(csv_data)} LTAs from {file_name}.")
        else:
            logger.warning(
                f"Issue in reading {file_name} from S3 bucket - file may be empty."
            )

        return csv_data
    except Exception as e:
        logger.error(f"Error reading {file_name} from S3: {str(e)}")
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
