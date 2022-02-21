import datetime
from typing import List

import factory
import factory.fuzzy

from transit_odp.otc.constants import (
    LicenceDescription,
    LicenceStatuses,
    SubsidiesDescription,
    TrafficAreas,
)
from transit_odp.otc.models import Licence as LicenceModel
from transit_odp.otc.models import Operator as OperatorModel
from transit_odp.otc.models import Service as ServiceModel
from transit_odp.otc.registry import Licence, Operator, Registration, Service

TODAY = datetime.date.today()
PAST = TODAY - datetime.timedelta(weeks=100)
DATE_STRING = "%d/%m/%y"


def fuzzy_date_as_text(_):
    return factory.fuzzy.FuzzyDate(start_date=PAST).fuzz().strftime(DATE_STRING)


class RegistrationFactory(factory.Factory):
    class Meta:
        model = Registration

    variation_number = factory.fuzzy.FuzzyInteger(low=1, high=100)
    service_number = factory.Sequence(lambda n: n)
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
    service_number = factory.Sequence(lambda n: n)
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
    service_type_description = factory.Faker("sentence", nb_words=4)
    short_notice = factory.fuzzy.FuzzyChoice([True, False])
    subsidies_description = factory.fuzzy.FuzzyChoice(SubsidiesDescription.values)
    subsidies_details = factory.Faker("sentence")


class LicenceModelFactory(factory.DjangoModelFactory, LicenceFactory):
    class Meta:
        model = LicenceModel


class OperatorModelFactory(factory.DjangoModelFactory, OperatorFactory):
    class Meta:
        model = OperatorModel


class ServiceModelFactory(factory.DjangoModelFactory, ServiceFactory):
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

        registrations.append(RegistrationFactory(**kwargs))

    return registrations
