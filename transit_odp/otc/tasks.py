from logging import getLogger

from celery import shared_task

from transit_odp.otc.loaders import Loader
from transit_odp.otc.registry import Registry

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
