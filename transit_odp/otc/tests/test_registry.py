import pytest

from transit_odp.otc.constants import CSV_FILE_TEMPLATE, OTC_CSV_URL
from transit_odp.otc.factories import (
    LicenceFactory,
    OperatorFactory,
    ServiceFactory,
    flatten_data,
)
from transit_odp.otc.registry import Registry
from transit_odp.otc.tests.conftest import CSV_DATA

pytestmark = pytest.mark.django_db


def test_one_operator_five_services_with_same_licence():
    operator = OperatorFactory()
    licence = LicenceFactory(number="PD0000007")
    services = [ServiceFactory(operator=operator, licence=licence) for _ in range(5)]
    registrations = flatten_data(services)
    registry = Registry(registrations)

    assert len(registry.operators) == 1
    assert len(registry.licences) == 1
    assert len(registry.services) == 5


def test_an_operator_having_multiple_licences():
    operator = OperatorFactory()
    l1 = LicenceFactory(number="LD0000007")
    l2 = LicenceFactory(number="LD0000008")
    services = ServiceFactory.create_batch(3, operator=operator, licence=l1)
    services += ServiceFactory.create_batch(3, operator=operator, licence_number=l2)
    services += ServiceFactory.create_batch(4)

    registrations = flatten_data(services)
    registry = Registry(registrations)

    assert len(registry.operators) == 5
    assert len(registry.services) == 10


def test_five_operators_five_services():
    services = [ServiceFactory() for _ in range(5)]
    registrations = flatten_data(services)
    registry = Registry(registrations)

    assert len(registry.operators) == 5
    assert len(registry.services) == 5
    assert len(registry.licences) == 5


@pytest.mark.parametrize(
    "cta,no_of_registration,no_of_operators,no_of_services,no_of_licences",
    CSV_DATA,
)
def test_otc_file_successfully_normalised(
    otc_urls, cta, no_of_registration, no_of_operators, no_of_services, no_of_licences
):
    url = f"{OTC_CSV_URL}/{CSV_FILE_TEMPLATE.format(cta)}"
    registry = Registry.from_url(url)

    assert len(registry.registrations) == no_of_registration
    assert len(registry.operators) == no_of_operators
    assert len(registry.services) == no_of_services
    assert len(registry.licences) == no_of_licences
