import datetime

import factory
import faker

from transit_odp.fares.models import DataCatalogueMetaData, FaresMetadata
from transit_odp.organisation.factories import DatasetMetadataFactory
from factory.django import DjangoModelFactory

FAKER = faker.Faker()


class FaresMetadataFactory(DatasetMetadataFactory):
    class Meta:
        model = FaresMetadata

    num_of_fare_zones = factory.Sequence(lambda n: n)
    num_of_lines = factory.Sequence(lambda n: n)
    num_of_sales_offer_packages = factory.Sequence(lambda n: n)
    num_of_fare_products = factory.Sequence(lambda n: n)
    num_of_user_profiles = factory.Sequence(lambda n: n)
    num_of_trip_products = factory.Sequence(lambda n: n)
    num_of_pass_products = factory.Sequence(lambda n: n)
    valid_from = datetime.datetime(2000, 5, 7)
    valid_to = datetime.datetime(2099, 5, 7)

    @factory.post_generation
    def stops(self, create, extracted, **kwargs):
        if not create:
            # simple build, do nothing
            return
        if extracted:
            # A list of groups were passed in, use them
            for stop in extracted:
                self.stops.add(stop)


class DataCatalogueMetaDataFactory(DjangoModelFactory):
    class Meta:
        model = DataCatalogueMetaData

    fares_metadata = factory.SubFactory(FaresMetadataFactory)
    atco_area = ["329"]
    valid_from = datetime.datetime(2000, 5, 7)
    valid_to = datetime.datetime(2099, 5, 7)
    line_id = ["123"]
    line_name = ["234"]
    national_operator_code = ["NR"]
    product_name = ["Adult Single"]
    product_type = ["dayPass"]
    tariff_basis = ["zone"]
    user_type = ["adult"]
    xml_file_name = FAKER.file_name(extension="xml")
