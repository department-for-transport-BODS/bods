import factory
from django.contrib.gis.geos import Point
import faker

from transit_odp.naptan.models import (
    AdminArea,
    District,
    Locality,
    StopPoint,
    FlexibleZone,
)

from factory.django import DjangoModelFactory
from transit_odp.otc.factories import UILtaFactory


class DistrictFactory(DjangoModelFactory):
    class Meta:
        model = District

    name = factory.Faker("street_name")


class AdminAreaFactory(DjangoModelFactory):
    class Meta:
        model = AdminArea

    atco_code = factory.Sequence(lambda n: n)  # unique atco code
    name = factory.Faker("street_name")
    traveline_region_id = factory.Faker("pystr", min_chars=12, max_chars=12)


class AdminAreaUILTAFactory(DjangoModelFactory):
    class Meta:
        model = AdminArea

    atco_code = factory.Sequence(lambda n: n)  # unique atco code
    name = factory.Faker("street_name")
    traveline_region_id = factory.Faker("pystr", min_chars=12, max_chars=12)
    ui_lta = factory.SubFactory(UILtaFactory)


class LocalityFactory(DjangoModelFactory):
    class Meta:
        model = Locality

    gazetteer_id = factory.Sequence(lambda n: n)  # unique id
    name = factory.Faker("street_name")
    district = factory.SubFactory(DistrictFactory)
    admin_area = factory.SubFactory(AdminAreaFactory)
    easting = 0
    northing = 0


class StopPointFactory(DjangoModelFactory):
    class Meta:
        model = StopPoint

    atco_code = factory.Sequence(lambda n: n)  # unique atco code
    naptan_code = factory.Faker("pystr", min_chars=12, max_chars=12)
    common_name = factory.Faker("street_name")
    street = factory.Faker("street_address")

    locality = factory.SubFactory(LocalityFactory)
    admin_area = factory.SubFactory(AdminAreaFactory)
    stop_areas = ["area1"]
    stop_type = factory.Faker("street_name")
    bus_stop_type = factory.Faker("street_name")

    @factory.lazy_attribute
    def location(self):
        fake = faker.Faker()
        location = fake.local_latlng(country_code="GB", coords_only=True)
        return Point(x=float(location[1]), y=float(location[0]), srid=4326)


class FlexibleZoneFactory(DjangoModelFactory):
    class Meta:
        model = FlexibleZone

    sequence_number = factory.Sequence(lambda n: n)
    naptan_stoppoint = factory.SubFactory(StopPointFactory)

    @factory.lazy_attribute
    def location(self):
        fake = faker.Faker()
        location = fake.local_latlng(country_code="GB", coords_only=True)
        return Point(x=float(location[1]), y=float(location[0]), srid=4326)
