import datetime
from typing import List

import factory
from factory.fuzzy import FuzzyDate, FuzzyInteger, FuzzyText, FuzzyChoice

from transit_odp.naptan.factories import StopPointFactory
from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.transmodel.models import (
    BankHolidays,
    NonOperatingDatesExceptions,
    OperatingDatesExceptions,
    OperatingProfile,
    Service,
    ServicePattern,
    ServicePatternStop,
    ServicedOrganisationVehicleJourney,
    ServicedOrganisationWorkingDays,
    ServicedOrganisations,
    VehicleJourney,
    StopActivity,
)
from factory.django import DjangoModelFactory

direction_choices = ["inbound", "outbound"]
day_choices = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class ServicePatternFactory(DjangoModelFactory):
    class Meta:
        model = ServicePattern

    service_pattern_id = factory.Sequence(lambda n: n)  # unique id
    revision = factory.SubFactory(DatasetRevisionFactory)
    origin = factory.Faker("street_name")
    destination = factory.Faker("street_name")
    description = factory.Faker("paragraph")
    line_name = FuzzyText(length=255)

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
    txcfileattributes = factory.SubFactory(TXCFileAttributesFactory)

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


class VehicleJourneyFactory(DjangoModelFactory):
    class Meta:
        model = VehicleJourney

    start_time = factory.Faker("time", format="%H:%M:%S")
    line_ref = FuzzyText(length=255)
    journey_code = FuzzyText(length=255)
    direction = FuzzyChoice(direction_choices)
    departure_day_shift = factory.Faker("boolean")
    service_pattern = factory.SubFactory(ServicePatternStopFactory)
    block_number = FuzzyInteger(1, 10)


class ServiceServicePatternFactory(DjangoModelFactory):
    class Meta:
        model = Service.service_patterns.through

    service = factory.SubFactory(ServiceFactory)
    servicepattern = factory.SubFactory(ServicePatternFactory)


class OperatingDatesExceptionsFactory(DjangoModelFactory):
    class Meta:
        model = OperatingDatesExceptions

    vehicle_journey = factory.SubFactory(VehicleJourneyFactory)
    operating_date = FuzzyDate(datetime.date.today())


class NonOperatingDatesExceptionsFactory(DjangoModelFactory):
    class Meta:
        model = NonOperatingDatesExceptions

    vehicle_journey = factory.SubFactory(VehicleJourneyFactory)
    non_operating_date = FuzzyDate(datetime.date.today())


class OperatingProfileFactory(DjangoModelFactory):
    class Meta:
        model = OperatingProfile

    vehicle_journey = factory.SubFactory(VehicleJourneyFactory)
    day_of_week = FuzzyChoice(day_choices)


class ServicedOrganisationsFactory(DjangoModelFactory):
    class Meta:
        model = ServicedOrganisations

    organisation_code = FuzzyText(length=255)
    name = FuzzyText(length=255)


class ServicedOrganisationVehicleJourneyFactory(DjangoModelFactory):
    class Meta:
        model = ServicedOrganisationVehicleJourney

    serviced_organisation = factory.SubFactory(ServicedOrganisationsFactory)
    vehicle_journey = factory.SubFactory(VehicleJourneyFactory)
    operating_on_working_days = factory.Faker("boolean")


class ServicedOrganisationWorkingDaysFactory(DjangoModelFactory):
    class Meta:
        model = ServicedOrganisationWorkingDays

    serviced_organisation_vehicle_journey = factory.SubFactory(
        ServicedOrganisationVehicleJourneyFactory
    )
    start_date = FuzzyDate(datetime.date.today())
    end_date = FuzzyDate(datetime.date.today())


class StopActivityFactory(DjangoModelFactory):
    class Meta:
        model = StopActivity

    name = FuzzyText(length=255)
    is_pickup = FuzzyChoice(choices=[True, False])
    is_setdown = FuzzyChoice(choices=[True, False])
    is_driverrequest = FuzzyChoice(choices=[True, False])
