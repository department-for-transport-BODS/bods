import datetime
from typing import List

import factory
from factory.fuzzy import FuzzyDate, FuzzyInteger, FuzzyText, FuzzyChoice

from transit_odp.naptan.factories import StopPointFactory
from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.transmodel.models import (
    BankHolidays,
    Service,
    ServicePattern,
    ServicePatternStop,
    ServicedOrganisations,
    StopActivity,
)
from factory.django import DjangoModelFactory


class ServicePatternFactory(DjangoModelFactory):
    class Meta:
        model = ServicePattern

    service_pattern_id = factory.Sequence(lambda n: n)  # unique id
    revision = factory.SubFactory(DatasetRevisionFactory)
    origin = factory.Faker("street_name")
    destination = factory.Faker("street_name")
    description = factory.Faker("paragraph")

    @factory.post_generation
    def stops(self, create, extracted: List[StopPoint], **kwargs):
        """Associates ServicePattern with Stops"""
        if not create:
            # simple build, do nothing
            return
        if extracted:
            # A list of groups were passed in, use them
            for stop in extracted:
                ServicePatternStopFactory.create(service_pattern=self, naptan_stop=stop)

    @factory.post_generation
    def service_links(self, create, extracted, **kwargs):
        if not create:
            # simple build, do nothing
            return
        if extracted:
            # A list of groups were passed in, use them
            for service_link in extracted:
                self.service_links.add(service_link)

    @factory.post_generation
    def admin_areas(self, create, extracted, **kwargs):
        if not create:
            # simple build, do nothing
            return
        if extracted:
            # A list of groups were passed in, use them
            for admin_area in extracted:
                self.admin_areas.add(admin_area)

    @factory.post_generation
    def localities(self, create, extracted, **kwargs):
        if not create:
            # simple build, do nothing
            return
        if extracted:
            # A list of groups were passed in, use them
            for locality in extracted:
                self.localities.add(locality)


class ServiceFactory(DjangoModelFactory):
    class Meta:
        model = Service

    revision = factory.SubFactory(DatasetRevisionFactory)
    service_code = FuzzyInteger(1, 10)
    name = FuzzyText(length=12)
    start_date = FuzzyDate(datetime.date.today())
    end_date = FuzzyDate(datetime.date.today())

    @factory.post_generation
    def service_patterns(self, create, extracted, **kwargs):
        if not create:
            # simple build, do nothing
            return

        if extracted:
            # A list of groups were passed in, use them
            for service_pattern in extracted:
                self.service_patterns.add(service_pattern)


class ServicePatternStopFactory(DjangoModelFactory):
    """Factory for ServicePatternStop through model"""

    class Meta:
        model = ServicePatternStop

    service_pattern = factory.SubFactory(ServicePatternFactory)
    naptan_stop = factory.SubFactory(StopPointFactory)
    sequence_number = factory.Sequence(
        lambda n: n
    )  # note this will be global, not sequenced per service_pattern
    atco_code = factory.Sequence(lambda n: n)


class ServicedOrganisationsFactory(DjangoModelFactory):
    class Meta:
        model = ServicedOrganisations

    organisation_code = FuzzyText(length=5)
    name = FuzzyText(length=12)


class BankHolidaysFactory(DjangoModelFactory):
    class Meta:
        model = BankHolidays

    txc_element = FuzzyText(length=255)
    title = FuzzyText(length=255)
    date = FuzzyDate(datetime.date.today())
    notes = FuzzyText(length=255)
    division = FuzzyText(length=255)


class StopActivityFactory(DjangoModelFactory):
    class Meta:
        model = StopActivity

    name = FuzzyText(length=255)
    is_pickup = FuzzyChoice(choices=[True, False])
    is_setdown = FuzzyChoice(choices=[True, False])
    is_driverrequest = FuzzyChoice(choices=[True, False])
