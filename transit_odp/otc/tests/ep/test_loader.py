import pandas as pd
import pytest

from transit_odp.otc.factories import EPServiceFactory
from transit_odp.otc.models import Service
from transit_odp.otc.ep.client import APIResponse
from transit_odp.otc.ep.loaders import Loader
from transit_odp.otc.ep.registry import Registry
from transit_odp.otc.constants import API_TYPE_EP

pytestmark = pytest.mark.django_db


@pytest.fixture
def get_ep_response(get_ep_data):
    ep_data = APIResponse(**get_ep_data)
    services_list = [service.model_dump() for service in ep_data.Results]
    service_df = pd.DataFrame(services_list)
    service_df["licence_id"] = None
    service_df["operator_id"] = None
    # drop column operator_name
    if "operator_name" in service_df.columns:
        service_df.drop(["operator_name"], axis=1, inplace=True)
    return service_df


class MockRegistry:
    def __init__(self, ep_data) -> None:
        self.services = ep_data

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
    EPServiceFactory.create_batch(total)

    loader = Loader(Registry())
    total_services = Service.objects.filter(api_type=API_TYPE_EP).count()
    loader.delete_services()
    total_after_delete = Service.objects.filter(api_type=API_TYPE_EP).count()

    assert total_services == total
    assert total_after_delete == 0


@pytest.mark.django_db
def test_load_services_method(get_ep_response):
    loader = Loader(MockRegistry(get_ep_response))
    loader.load_services()

    total_services = Service.objects.filter(api_type=API_TYPE_EP).count()
    assert total_services == 5


@pytest.mark.django_db
def test_load_method_with_Response(get_ep_response):
    loader = Loader(MockRegistry(get_ep_response))
    loader.load()

    total_services = Service.objects.filter(api_type=API_TYPE_EP).count()
    total_services_without_licence = Service.objects.filter(
        licence_id__isnull=True
    ).count()
    assert total_services == 5
    assert total_services_without_licence == 0


@pytest.mark.django_db
def test_load_method_blank_Response():
    loader = Loader(MockRegistry(pd.DataFrame()))
    loader.load()

    total_services = Service.objects.filter(api_type=API_TYPE_EP).count()
    assert total_services == 0
