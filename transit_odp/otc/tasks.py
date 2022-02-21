from logging import getLogger

from celery import shared_task

from transit_odp.otc.constants import CSV_FILE_TEMPLATE, OTC_CSV_URL, TrafficAreas
from transit_odp.otc.loaders import Loader
from transit_odp.otc.registry import Registry

logger = getLogger(__name__)


@shared_task()
def task_refresh_otc_data():
    url = f"{OTC_CSV_URL}/{CSV_FILE_TEMPLATE}"
    urls = [url.format(ta) for ta in TrafficAreas.values]
    registry = Registry.from_url(urls)
    logger.info(f"retrieved {len(registry.registrations)} records from OTC")

    loader = Loader(registry)
    loader.load()
