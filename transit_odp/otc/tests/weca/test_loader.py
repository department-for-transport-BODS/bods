import pandas as pd
import pytest

from transit_odp.otc.factories import WecaServiceFactory
from transit_odp.otc.models import Service
from transit_odp.otc.tests.conftest import get_weca_data
from transit_odp.otc.weca.client import APIResponse
from transit_odp.otc.weca.loaders import Loader
from transit_odp.otc.weca.registry import Registry
from transit_odp.otc.constants import API_TYPE_WECA

pytestmark = pytest.mark.django_db


def get_weca_response():
    weca_data = APIResponse(**get_weca_data())
    services_list = [service.model_dump() for service in weca_data.data]
    service_df = pd.DataFrame(services_list)
    service_df["licence_id"] = None
    return service_df


class MockRegistry:
    def __init__(self, weca_data) -> None:
        self.services = weca_data

    def fetch_all_records(self):
        pass

    def process_services(self):
        pass

    def get_missing_licences(self):
        registry = Registry()
        registry.services = self.services
        return registry.get_missing_licences()


@pytest.mark.django_db
def test_delete_services():
    total = 5
    WecaServiceFactory.create_batch(total)

    loader = Loader(Registry())
    total_services = Service.objects.filter(api_type=API_TYPE_WECA).count()
    loader.delete_services()
    total_after_delete = Service.objects.filter(api_type=API_TYPE_WECA).count()

    assert total_services == total
    assert total_after_delete == 0


@pytest.mark.django_db
def test_load_services_method():
    loader = Loader(MockRegistry(get_weca_response()))
    loader.load_services()

    total_services = Service.objects.filter(api_type=API_TYPE_WECA).count()
    assert total_services == 5


@pytest.mark.django_db
def test_load_method_with_Response():
    loader = Loader(MockRegistry(get_weca_response()))
    loader.load()

    total_services = Service.objects.filter(api_type=API_TYPE_WECA).count()
    total_services_without_licence = Service.objects.filter(
        licence_id__isnull=True
    ).count()
    assert total_services == 5
    assert total_services_without_licence == 0


@pytest.mark.django_db
def test_load_method_blank_Response():
    loader = Loader(MockRegistry(pd.DataFrame()))
    loader.load()

    total_services = Service.objects.filter(api_type=API_TYPE_WECA).count()
    assert total_services == 0


@pytest.mark.django_db
def test_load_method_blank_Response_preexisting_services():
    # load 5 services in the db
    WecaServiceFactory.create_batch(5)

    # after we receive blank, it will keep the old state as it is,
    loader = Loader(MockRegistry(pd.DataFrame()))
    loader.load()

    total_services = Service.objects.filter(api_type=API_TYPE_WECA).count()
    assert total_services == 5
