from logging import getLogger

from celery import shared_task

from transit_odp.naptan.models import AdminArea
from transit_odp.otc.ep.loaders import Loader as EPLoader
from transit_odp.otc.ep.registry import Registry as EPRegistry
from transit_odp.otc.loaders import Loader
from transit_odp.otc.loaderslta import LoaderLTA
from transit_odp.otc.models import LocalAuthority as OTCLocalAuthority
from transit_odp.otc.populate_lta import PopulateLTA
from transit_odp.otc.registry import Registry
from transit_odp.otc.weca.loaders import Loader as WecaLoader
from transit_odp.otc.weca.registry import Registry as WecaRegistry

from .utils import (
    check_missing_csv_lta_names,
    get_ui_lta,
    read_local_authority_comparison_file_from_s3_bucket,
)

logger = getLogger(__name__)


@shared_task()
def task_refresh_otc_data():
    registry = Registry()
    loader = Loader(registry)
    loader.load()


@shared_task()
def task_get_all_otc_data():
    registry = Registry()
    loader = Loader(registry)
    loader.load_into_fresh_database()


@shared_task()
def task_refresh_weca_data():
    registry = WecaRegistry()
    loader = WecaLoader(registry)
    loader.load()


@shared_task(ignore_errors=True)
def task_populate_lta_data():
    populate_lta = PopulateLTA()
    loader = LoaderLTA(populate_lta)
    loader.load_lta_into_fresh_database()


@shared_task()
def task_refresh_ep_data():
    registry = EPRegistry()
    loader = EPLoader(registry)
    loader.load()


@shared_task()
def task_populate_ui_lta_data():
    """
    A one-off task that populates the UI LTA-related data. A file
    is read from the S3 bucket and the OTCLocalAuthority and AdminArea
    tables are populated.
    """
    logger.info("Populating UI LTA data.")
    csv_data = read_local_authority_comparison_file_from_s3_bucket()

    logger.info("Checking for missing CSV LTA names.")

    missing_lta_names = check_missing_csv_lta_names(csv_data)

    if len(missing_lta_names) == 0:
        logger.info(
            f"There are no LTAs that are present in the OTC database and have not been added to the LTA relationships CSV."
        )

    if missing_lta_names:
        missing_lta_names_list = ", ".join(missing_lta_names)
        logger.info(
            f"These LTAs are present in the OTC database but have not been added to the LTA relationships CSV: {missing_lta_names_list}"
        )

    for lta_dict in csv_data:
        otc_name = lta_dict["OTC name"]
        ui_name = lta_dict["UI name"]
        admin_area = lta_dict["Admin area"]

        if otc_name not in missing_lta_names:
            ui_lta_obj = get_ui_lta(ui_name)

            try:
                lta_obj = OTCLocalAuthority.objects.get(name=otc_name)
                admin_area_obj = AdminArea.objects.get(id=admin_area)
            except OTCLocalAuthority.DoesNotExist:
                logger.info(
                    f"The following LTA is not present in the Local Authority database: {otc_name}"
                )
                continue
            except AdminArea.DoesNotExist:
                logger.info(
                    f"The following admin area is not present in the Admin Area database: {admin_area}"
                )
                continue

            if ui_lta_obj:
                lta_obj.ui_lta_id = ui_lta_obj.id
                lta_obj.save()

                admin_area_obj.ui_lta_id = ui_lta_obj.id
                admin_area_obj.save()

    logger.info("Successfullly completed populating UI LTA data.")
