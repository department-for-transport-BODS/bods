from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from transit_odp.otc.client.enums import RegistrationStatusEnum
from transit_odp.otc.factories import (
    LicenceFactory,
    LicenceModelFactory,
    OperatorFactory,
    OperatorModelFactory,
    RegistrationFactory,
    ServiceFactory,
    ServiceModelFactory,
    flatten_data,
)
from transit_odp.otc.loaders import Loader, LoadFailedException
from transit_odp.otc.models import Licence, Operator, Service
from transit_odp.otc.registry import Registry

pytestmark = pytest.mark.django_db
HERE = Path(__file__)
CLIENT = "transit_odp.otc.client.otc_client.OTCAPIClient"
TODAY = date.today()
FUTURE = TODAY + timedelta(weeks=10)


def test_empty_database_raises():
    registry = Registry()
    loader = Loader(registry)
    with pytest.raises(LoadFailedException):
        loader.load()


@patch(f"{CLIENT}.get_latest_variations_since")
def test_simple_load(fake_client):
    # Need something in the database so we know when to request from
    ServiceModelFactory(operator__operator_id=99, licence__number="DF9999999")
    operator = OperatorFactory()
    l1 = LicenceFactory(number="LD0000007")
    l2 = LicenceFactory(number="LD0000008")
    services = ServiceFactory.create_batch(
        3, operator=operator, licence=l1, variation_number=0
    )
    services += ServiceFactory.create_batch(
        3, operator=operator, licence=l2, variation_number=0, effective_date=FUTURE
    )
    services += ServiceFactory.create_batch(2, effective_date=FUTURE)
    services += ServiceFactory.create_batch(2, effective_date=None)

    fake_client.return_value = flatten_data(services)
    registry = Registry()
    loader = Loader(registry)
    loader.load()

    assert Operator.objects.count() == 5 + 1
    assert Service.objects.count() == 7 + 1
    assert Licence.objects.count() == 5 + 1


@patch(f"{CLIENT}.get_latest_variations_since")
def test_services_types_on_same_registrations_are_added(fake_client):
    ServiceModelFactory(operator__operator_id=99, licence__number="DF9999999")
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

    fake_client.return_value = flatten_data([s1, s2, s3])
    registry = Registry()
    loader = Loader(registry)
    loader.load()

    assert Operator.objects.count() == 1 + 1
    assert Service.objects.count() == 3 + 1
    assert Licence.objects.count() == 1 + 1


@patch(f"{CLIENT}.get_latest_variations_since")
def test_services_types_on_same_registrations_are_updated(fake_client):
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

    fake_client.return_value = flatten_data([s1, s2, s3])
    registry = Registry()
    loader = Loader(registry)
    loader.load()

    for service in Service.objects.all():
        assert service.public_text == "Updated"
        assert service.licence.granted_date == datetime(2021, 12, 25, 12, 1, 1).date()
        assert service.operator.address == "North Pole"


@patch(f"{CLIENT}.get_latest_variations_since")
def test_can_create_new_services_with_existing_services(fake_client):
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

    fake_client.return_value = flatten_data(absent + present + more_present)
    registry = Registry()
    loader = Loader(registry)

    db_operators = set(Operator.objects.values_list("operator_id", flat=True))
    db_services = set(
        Service.objects.values_list("registration_number", "service_type_description")
    )
    db_licences = set(Licence.objects.values_list("number", flat=True))

    assert db_operators.isdisjoint(loader.get_missing_operators())
    assert db_services.isdisjoint(loader.get_missing_services())
    assert db_licences.isdisjoint(loader.get_missing_licences())


@patch(f"{CLIENT}.get_latest_variations_since")
def test_can_update_modified_variations(fake_client):
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

    fake_client.return_value = flatten_data(
        new_services_updated + new_services_not_updated
    )
    registry = Registry()
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


@patch(f"{CLIENT}.get_latest_variations_since")
def test_can_delete_cancelled_variations(fake_client):
    OperatorModelFactory.reset_sequence(1)
    LicenceModelFactory.reset_sequence(1)
    ServiceFactory.reset_sequence(5)
    OperatorFactory.reset_sequence(10)
    LicenceFactory.reset_sequence(10)
    existing_services = ServiceFactory.create_batch(5)
    services_should_not_to_delete = ServiceFactory.create_batch(
        2,
        effective_date=FUTURE,
        registration_status=RegistrationStatusEnum.CANCELLED.value,
    )
    services_to_delete = ServiceFactory.create_batch(5)
    licence_expiry_date = datetime(2021, 12, 25, 12, 1, 1).date()

    # Need to create data both in the database and in the API
    for service in existing_services:
        service_kwargs = service.dict()
        operator_kwargs = service_kwargs.pop("operator")
        licence_kwargs = service_kwargs.pop("licence")
        operator = OperatorModelFactory(**operator_kwargs)
        licence = LicenceModelFactory(**licence_kwargs)
        ServiceModelFactory(**service_kwargs, operator=operator, licence=licence)

    for service in services_should_not_to_delete:
        service_kwargs = service.dict()
        operator_kwargs = service_kwargs.pop("operator")
        licence_kwargs = service_kwargs.pop("licence")
        operator = OperatorModelFactory(**operator_kwargs)
        licence = LicenceModelFactory(**licence_kwargs)
        ServiceModelFactory(**service_kwargs, operator=operator, licence=licence)

    # Cause a delete to trigger the delete code
    for service in services_to_delete:
        service_kwargs = service.dict()
        operator_kwargs = service_kwargs.pop("operator")
        operator = OperatorModelFactory(**operator_kwargs)
        licence_kwargs = service_kwargs.pop("licence")
        licence = LicenceModelFactory(**licence_kwargs)
        ServiceModelFactory(**service_kwargs, operator=operator, licence=licence)

        operator_name = service.operator.operator_name
        service.operator.operator_name = f"DELETED - {operator_name}"
        service.variation_number += 1
        service.public_text = "A delete happened"
        service.licence.expiry_date = licence_expiry_date
        service.registration_status = RegistrationStatusEnum.CANCELLED.value

    registrations = flatten_data(
        services_to_delete + existing_services + services_should_not_to_delete
    )
    registry = Registry()
    for registration in registrations:
        registry.update(registration)

    loader = Loader(registry)
    loader.load_licences()
    loader.load_operators()
    loader.load_services()
    assert Service.objects.count() == len(
        existing_services + services_to_delete + services_should_not_to_delete
    ), "no new objects created"

    loader.update_services_and_operators()
    assert (
        Service.objects.filter(public_text="A delete happened").count() == 0
    ), "test no service update happened"
    assert (
        Licence.objects.filter(expiry_date=licence_expiry_date).count() == 0
    ), "test no licence update happened"
    assert (
        Operator.objects.filter(operator_name__startswith="Deleted").count() == 0
    ), "test no operator update happened"

    loader.delete_bad_data()

    assert Service.objects.count() == len(
        existing_services + services_should_not_to_delete
    )


@patch("transit_odp.otc.registry.Registry.add_all_latest_registered_variations")
@patch("transit_odp.otc.registry.Registry.add_all_older_registered_variations")
def test_long_start_point_is_accepted(mock1, mock2):
    mock1.return_value = []
    mock2.return_value = []
    registry = Registry()
    registrations = RegistrationFactory.create_batch(5)
    registrations.append(
        RegistrationFactory(
            start_point="a place with a reallyreallyreallyreallyreallyreallyreally"
            "reallyreallyreallyreallyreallyreallyreallyreally long name"
        )
    )
    for registration in registrations:
        registry.update(registration)

    loader = Loader(registry)
    loader.load_into_fresh_database()
