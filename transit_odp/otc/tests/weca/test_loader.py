import pytest
from transit_odp.otc.factories import WecaServiceFactory
from transit_odp.otc.weca.loaders import Loader
from transit_odp.otc.weca.registry import Registry
from transit_odp.otc.models import Service

pytestmark = pytest.mark.django_db

@pytest.mark.django_db
def test_delete_services():
    total = 5
    services = WecaServiceFactory.create_batch(total)

    loader = Loader(Registry())
    print(Service.objects.filter(api_type="WECA").count())
    total_services = Service.objects.filter(api_type="WECA").count()
    loader.delete_services()
    total_after_delete = Service.objects.filter(api_type="WECA").count()

    assert(total_services == total)
    assert(total_after_delete == 0)

# @pytest.mark.django_db
# def test_load_services_mothod():
#     total = 5

#     loader = Loader(Registry())
#     print(Service.objects.filter(api_type="WECA").count())
#     total_services = Service.objects.filter(api_type="WECA").count()
#     loader.delete_services()
#     total_after_delete = Service.objects.filter(api_type="WECA").count()

#     assert(total_services == total)
#     assert(total_after_delete == 0)