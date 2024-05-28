from datetime import datetime, timedelta
from logging import getLogger

from celery import shared_task

from transit_odp.otc.loaders import Loader
from transit_odp.otc.registry import Registry
from transit_odp.otc.weca.registry import Registry as WecaRegistry
from transit_odp.otc.weca.loaders import Loader as WecaLoader
from transit_odp.otc.populate_lta import PopulateLTA
from transit_odp.otc.loaderslta import LoaderLTA
from transit_odp.otc.ep.registry import Registry as EPRegistry
from transit_odp.otc.ep.loaders import Loader as EPLoader

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
