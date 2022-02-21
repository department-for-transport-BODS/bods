from datetime import datetime
from pathlib import Path

import pytest

from transit_odp.otc.constants import CSV_FILE_TEMPLATE, TrafficAreas
from transit_odp.otc.factories import (
    LicenceFactory,
    LicenceModelFactory,
    OperatorFactory,
    OperatorModelFactory,
    ServiceFactory,
    ServiceModelFactory,
    flatten_data,
)
from transit_odp.otc.loaders import Loader
from transit_odp.otc.models import Licence, Operator, Service
from transit_odp.otc.registry import Registry
from transit_odp.otc.tests.conftest import CSV_DATA

pytestmark = pytest.mark.django_db
HERE = Path(__file__)
CSV_PATH = HERE.parent / Path("data")


def test_can_successfully_load_models_empty_database():
    operator = OperatorFactory()
    l1 = LicenceFactory(number="LD0000007")
    l2 = LicenceFactory(number="LD0000008")
    services = ServiceFactory.create_batch(3, operator=operator, licence=l1)
    services += ServiceFactory.create_batch(3, operator=operator, licence=l2)
    services += ServiceFactory.create_batch(4)

    registrations = flatten_data(services)
    registry = Registry(registrations)
    loader = Loader(registry)
    loader.load()

    assert Operator.objects.count() == 5
    assert Service.objects.count() == 10
    assert Licence.objects.count() == 6


def test_services_types_on_same_registrations_are_added():
    o = OperatorFactory()
    l1 = LicenceFactory(number="LD0000007")
    reg_number = l1.number + "/42"
    s1 = ServiceFactory(
        operator=o,
        licence=l1,
        registration_number=reg_number,
        service_type_description="circular",
    )
    s2 = ServiceFactory(
        operator=o,
        licence=l1,
        registration_number=reg_number,
        service_type_description="school run",
    )
    s3 = ServiceFactory(
        operator=o,
        licence=l1,
        registration_number=reg_number,
        service_type_description="",
    )

    registrations = flatten_data([s1, s2, s3])
    registry = Registry(registrations)
    loader = Loader(registry)
    loader.load()

    assert Operator.objects.count() == 1
    assert Service.objects.count() == 3
    assert Licence.objects.count() == 1


def test_services_types_on_same_registrations_are_updated():
    new_op = OperatorFactory()
    new_lic = LicenceFactory(number="LD0000007")
    o = OperatorModelFactory(**new_op.dict())
    l1 = LicenceModelFactory(**new_lic.dict())
    reg_number = l1.number + "/42"
    ServiceModelFactory(
        operator=o,
        licence=l1,
        registration_number=reg_number,
        service_type_description="circular",
        variation_number=0,
    )
    ServiceModelFactory(
        operator=o,
        licence=l1,
        registration_number=reg_number,
        service_type_description="school run",
        variation_number=0,
    )
    ServiceModelFactory(
        operator=o,
        licence=l1,
        registration_number=reg_number,
        service_type_description="",
        variation_number=0,
    )

    new_lic.granted_date = datetime(2021, 12, 25, 12, 1, 1).date()
    new_op.address = "North Pole"

    s1 = ServiceFactory(
        operator=new_op,
        licence=new_lic,
        registration_number=reg_number,
        service_type_description="circular",
        variation_number=1,
        public_text="Updated",
    )
    s2 = ServiceFactory(
        operator=new_op,
        licence=new_lic,
        registration_number=reg_number,
        service_type_description="school run",
        variation_number=1,
        public_text="Updated",
    )
    s3 = ServiceFactory(
        operator=new_op,
        licence=new_lic,
        registration_number=reg_number,
        service_type_description="",
        variation_number=1,
        public_text="Updated",
    )

    registrations = flatten_data([s1, s2, s3])
    registry = Registry(registrations)
    loader = Loader(registry)
    loader.load()

    for service in Service.objects.all():
        assert service.public_text == "Updated"
        assert service.licence.granted_date == datetime(2021, 12, 25, 12, 1, 1).date()
        assert service.operator.address == "North Pole"


def test_can_create_new_services_with_existing_services():
    operator = OperatorFactory()
    operator_model = OperatorModelFactory(**operator.dict())
    l1 = LicenceFactory(number="LD0000007")
    l2 = LicenceFactory(number="LD0000008")
    licence_model = LicenceModelFactory(**l2.dict())
    absent = ServiceFactory.create_batch(3, operator=operator, licence=l1)
    absent += ServiceFactory.create_batch(2)

    present = ServiceFactory.create_batch(3, operator=operator, licence=l2)
    for service in present:
        kwargs = service.dict()
        kwargs.pop("operator")
        kwargs.pop("licence")
        ServiceModelFactory(**kwargs, operator=operator_model, licence=licence_model)

    more_present = ServiceFactory.create_batch(2)
    for service in more_present:
        service_kwargs = service.dict()
        operator_kwargs = service_kwargs.pop("operator")
        licence_kwargs = service_kwargs.pop("licence")
        licence_model = LicenceModelFactory(**licence_kwargs)
        op = OperatorModelFactory(**operator_kwargs)
        ServiceModelFactory(**service_kwargs, operator=op, licence=licence_model)

    registrations = flatten_data(absent + present + more_present)
    registry = Registry(registrations)
    loader = Loader(registry)

    db_operators = set(Operator.objects.values_list("operator_id", flat=True))
    db_services = set(
        Service.objects.values_list("registration_number", "service_type_description")
    )
    db_licences = set(Licence.objects.values_list("number", flat=True))

    assert db_operators.isdisjoint(loader.get_missing_operators())
    assert db_services.isdisjoint(loader.get_missing_services())
    assert db_licences.isdisjoint(loader.get_missing_licences())


def test_can_update_modified_variations():
    OperatorModelFactory.reset_sequence(1)
    LicenceModelFactory.reset_sequence(1)
    ServiceModelFactory.create_batch(5)
    ServiceFactory.reset_sequence(5)
    OperatorFactory.reset_sequence(10)
    LicenceFactory.reset_sequence(10)
    new_services_not_updated = ServiceFactory.create_batch(5)
    new_services_updated = ServiceFactory.create_batch(5)

    # Need to create data both in the database and in the local csv
    for service in new_services_not_updated:
        service_kwargs = service.dict()
        operator_kwargs = service_kwargs.pop("operator")
        licence_kwargs = service_kwargs.pop("licence")
        operator = OperatorModelFactory(**operator_kwargs)
        licence = LicenceModelFactory(**licence_kwargs)
        ServiceModelFactory(**service_kwargs, operator=operator, licence=licence)

    # Cause a mismatch to trigger the update code
    for service in new_services_updated:
        service_kwargs = service.dict()
        operator_kwargs = service_kwargs.pop("operator")
        operator = OperatorModelFactory(**operator_kwargs)
        licence_kwargs = service_kwargs.pop("licence")
        licence = LicenceModelFactory(**licence_kwargs)
        ServiceModelFactory(**service_kwargs, operator=operator, licence=licence)

        operator_name = service.operator.operator_name
        service.operator.operator_name = f"UPDATED - {operator_name}"
        service.variation_number += 1
        service.public_text = "An update happened"
        service.licence.expiry_date = datetime(2021, 12, 25, 12, 1, 1).date()

    registrations = flatten_data(new_services_updated + new_services_not_updated)
    registry = Registry(registrations)
    loader = Loader(registry)
    loader.load()

    for service in new_services_updated:
        service = Service.objects.get(
            registration_number=service.registration_number,
            service_type_description=service.service_type_description,
        )
        assert service.public_text == "An update happened"
        assert service.operator.operator_name.startswith("UPDATED")
        assert service.licence.expiry_date == datetime(2021, 12, 25, 12, 1, 1).date()

    for service in new_services_not_updated:
        service = Service.objects.get(
            registration_number=service.registration_number,
            service_type_description=service.service_type_description,
        )
        assert service.public_text != "An update happened"
        assert not service.operator.operator_name.startswith("UPDATED")


def test_load_all_registrations():
    files = [CSV_PATH / CSV_FILE_TEMPLATE.format(ta) for ta in TrafficAreas.values]
    registry = Registry.from_filepath(files)
    loader = Loader(registry)
    loader.load()

    assert Operator.objects.count() == 908
    # expected 922 (sum of all CSVs) but there are duplicates across CSV's
    # 908 unique operator ids in total.
    assert Service.objects.count() == sum(row[3] for row in CSV_DATA) == 14268
    # all services accounted for, perhaps operators have services that span traffic
    # areas
    assert Licence.objects.count() == sum(row[4] for row in CSV_DATA) == 922
