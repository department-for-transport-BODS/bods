import datetime
from typing import List

import factory
import factory.fuzzy
from django.utils import timezone

from transit_odp.otc.constants import (
    LicenceDescription,
    LicenceStatuses,
    SubsidiesDescription,
    TrafficAreas,
)
from transit_odp.otc.dataclasses import Licence, Operator, Registration, Service
from transit_odp.otc.models import Licence as LicenceModel, UILta
from transit_odp.otc.models import LocalAuthority
from transit_odp.otc.models import Operator as OperatorModel
from transit_odp.otc.models import Service as ServiceModel
from factory.django import DjangoModelFactory

TODAY = datetime.date.today()
NOW = timezone.now()
PAST = TODAY - datetime.timedelta(weeks=100)
RECENT = NOW - datetime.timedelta(days=2)
DATE_STRING = "%d/%m/%Y"
DATETIME_STRING = "%d/%m/%Y %H:%M:%S"


def fuzzy_date_as_text(_):
    return factory.fuzzy.FuzzyDate(start_date=PAST).fuzz().strftime(DATE_STRING)


def fuzzy_datetime_as_text(_):
    return (
        factory.fuzzy.FuzzyDateTime(start_dt=RECENT, end_dt=NOW)
        .fuzz()
        .strftime(DATETIME_STRING)
    )


class RegistrationFactory(factory.Factory):
    class Meta:
        model = Registration

    variation_number = factory.fuzzy.FuzzyInteger(low=1, high=100)
    service_number = factory.Sequence(lambda n: str(n))
    current_traffic_area = factory.fuzzy.FuzzyChoice(TrafficAreas.values)
    licence_number = factory.Sequence(lambda n: f"PD0000{n:03}")
    discs_in_possession = factory.fuzzy.FuzzyInteger(low=100, high=400)
    authdiscs = 400
    licence_granted_date = factory.LazyAttribute(fuzzy_date_as_text)
    licence_expiry_date = factory.LazyAttribute(fuzzy_date_as_text)
    description = factory.fuzzy.FuzzyChoice(LicenceDescription.values)
    operator_id = factory.sequence(lambda n: n)
    operator_name = factory.Faker("company")
    trading_name = factory.LazyAttribute(lambda obj: obj.operator_name.upper())
    address = factory.Faker("address")
    start_point = factory.Faker("street_name")
    finish_point = factory.Faker("street_name")
    via = factory.Faker("sentence")
    effective_date = factory.LazyAttribute(fuzzy_date_as_text)
    received_date = factory.LazyAttribute(fuzzy_date_as_text)
    end_date = factory.LazyAttribute(fuzzy_date_as_text)
    service_type_other_details = factory.Faker("sentence")
    licence_status = factory.fuzzy.FuzzyChoice(LicenceStatuses.values)
    registration_status = "Registered"
    public_text = factory.Faker("paragraph")
    service_type_description = factory.Faker("sentence", nb_words=4)
    short_notice = factory.fuzzy.FuzzyChoice([True, False])
    subsidies_description = factory.fuzzy.FuzzyChoice(SubsidiesDescription.values)
    subsidies_details = factory.Faker("sentence")
    auth_description = "Council"
    tao_covered_by_area = factory.Faker("address")
    registration_code = factory.fuzzy.FuzzyInteger(high=20, low=1)
    registration_number = factory.LazyAttribute(
        lambda obj: f"{obj.licence_number}/{obj.registration_code}"
    )
    last_modified = factory.LazyAttribute(fuzzy_datetime_as_text)


class LicenceFactory(factory.Factory):
    class Meta:
        model = Licence

    number = factory.Sequence(lambda n: f"PD0000{n:03}")
    status = factory.fuzzy.FuzzyChoice(LicenceStatuses.values)
    granted_date = factory.fuzzy.FuzzyDate(start_date=PAST)
    expiry_date = factory.fuzzy.FuzzyDate(start_date=PAST)


class OperatorFactory(factory.Factory):
    class Meta:
        model = Operator

    discs_in_possession = factory.fuzzy.FuzzyInteger(low=100, high=400)
    authdiscs = 400
    operator_id = factory.sequence(lambda n: n)
    operator_name = factory.Faker("company")
    address = factory.Faker("address")


class ServiceFactory(factory.Factory):
    class Meta:
        model = Service

    licence = factory.SubFactory(LicenceFactory)
    registration_number = factory.LazyAttribute(
        lambda obj: f"{obj.licence.number}/{obj.registration_code}"
    )
    variation_number = factory.fuzzy.FuzzyInteger(low=1, high=100)
    service_number = factory.Sequence(lambda n: str(n))
    current_traffic_area = "B"
    operator = factory.SubFactory(OperatorFactory)
    start_point = factory.Faker("street_name")
    finish_point = factory.Faker("street_name")
    via = factory.Faker("sentence")
    effective_date = factory.fuzzy.FuzzyDate(start_date=PAST)
    received_date = factory.fuzzy.FuzzyDate(start_date=PAST)
    end_date = factory.fuzzy.FuzzyDate(start_date=PAST)
    service_type_other_details = factory.Faker("sentence")
    registration_code = factory.fuzzy.FuzzyInteger(high=20, low=1)
    description = factory.fuzzy.FuzzyChoice(LicenceDescription.values)
    registration_status = "Registered"
    public_text = factory.Faker("paragraph")
    service_type_description = factory.Faker("sentence", nb_words=2)
    short_notice = factory.fuzzy.FuzzyChoice([True, False])
    subsidies_description = factory.fuzzy.FuzzyChoice(SubsidiesDescription.values)
    subsidies_details = factory.Faker("sentence")
    last_modified = factory.fuzzy.FuzzyDateTime(start_dt=RECENT)

class WecaServiceFactory(DjangoModelFactory, factory.Factory):
    class Meta:
        model = ServiceModel

    registration_number = f"PH0000132/01010379"
    variation_number = 0
    service_number = factory.Sequence(lambda n: str(n))
    start_point = factory.Faker("street_name")
    finish_point = factory.Faker("street_name")
    via = factory.Faker("sentence")
    effective_date = factory.fuzzy.FuzzyDate(start_date=PAST)
    api_type = "WECA"
    atco_code = f"{factory.fuzzy.FuzzyInteger(high=999, low=100)}"


class UILtaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UILta

    name = factory.Faker("name")


class LocalAuthorityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LocalAuthority

    name = factory.Faker("name")
    ui_lta = factory.SubFactory(UILtaFactory)

    @factory.post_generation
    def registration_numbers(self, create, extracted, **kwargs):
        if not create:
            # simple build, do nothing
            return
        if extracted:
            # A list of groups were passed in, use them
            for reg_num in extracted:
                self.registration_numbers.add(reg_num)


class LicenceModelFactory(DjangoModelFactory, LicenceFactory):
    class Meta:
        model = LicenceModel


class OperatorModelFactory(DjangoModelFactory, OperatorFactory):
    class Meta:
        model = OperatorModel


class ServiceModelFactory(DjangoModelFactory, ServiceFactory):
    class Meta:
        model = ServiceModel

    operator = factory.SubFactory(OperatorModelFactory)
    licence = factory.SubFactory(LicenceModelFactory)


def flatten_data(services: List[Service]) -> List[Registration]:
    registrations = []
    for service in services:
        service_kwargs = service.dict()
        operator_kwargs = service_kwargs.pop("operator")
        licence_kwargs = {
            f"licence_{key}": value
            for key, value in service_kwargs.pop("licence").items()
        }
        kwargs = {**service_kwargs, **operator_kwargs, **licence_kwargs}
        for key, value in kwargs.items():
            if isinstance(value, datetime.date):
                kwargs[key] = value.strftime(DATE_STRING)
            if isinstance(value, datetime.datetime):
                kwargs[key] = value.strftime(DATETIME_STRING)

        registrations.append(RegistrationFactory(**kwargs))

    return registrations
