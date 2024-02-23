import pytest
from transit_odp.otc.factories import WecaServiceFactory
from transit_odp.otc.weca.loaders import Loader
from transit_odp.otc.weca.registry import Registry
from transit_odp.otc.models import Service
from transit_odp.otc.tests.conftest import get_weca_data
from transit_odp.otc.weca.client import APIResponse

pytestmark = pytest.mark.django_db


class MockRegistry:
    def __init__(self, weca_data) -> None:
        self.services = weca_data

    def fetch_all_records(self):
        pass


@pytest.mark.django_db
def test_delete_services():
    total = 5
    services = WecaServiceFactory.create_batch(total)

    loader = Loader(Registry())
    total_services = Service.objects.filter(api_type="WECA").count()
    loader.delete_services()
    total_after_delete = Service.objects.filter(api_type="WECA").count()

    assert total_services == total
    assert total_after_delete == 0


@pytest.mark.django_db
def test_load_services_method():
    weca_data = APIResponse(**get_weca_data())
    loader = Loader(MockRegistry(weca_data.data))
    loader.load_services()

    total_services = Service.objects.filter(api_type="WECA").count()
    assert total_services == 5


@pytest.mark.django_db
def test_load_method_with_Response():
    weca_data = APIResponse(**get_weca_data())
    loader = Loader(MockRegistry(weca_data.data))
    loader.load()

    total_services = Service.objects.filter(api_type="WECA").count()
    assert total_services == 5


@pytest.mark.django_db
def test_load_method_blank_Response():
    loader = Loader(MockRegistry([]))
    loader.load()

    total_services = Service.objects.filter(api_type="WECA").count()
    assert total_services == 0


@pytest.mark.django_db
def test_load_method_blank_Response_preexisting_services():
    # load 5 services in the db
    services = WecaServiceFactory.create_batch(5)

    # after we receive blank, it will keep the old state as it is,
    loader = Loader(MockRegistry([]))
    loader.load()

    total_services = Service.objects.filter(api_type="WECA").count()
    assert total_services == 5
