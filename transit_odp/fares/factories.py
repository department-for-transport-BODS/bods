import datetime

import factory
from waffle import flag_is_active

from transit_odp.fares.models import DataCatalogueMetaData, FaresMetadata
from transit_odp.organisation.factories import DatasetMetadataFactory


class FaresMetadataFactory(DatasetMetadataFactory):
    class Meta:
        model = FaresMetadata

    num_of_fare_zones = factory.Sequence(lambda n: n)
    num_of_lines = factory.Sequence(lambda n: n)
    num_of_sales_offer_packages = factory.Sequence(lambda n: n)
    num_of_fare_products = factory.Sequence(lambda n: n)
    num_of_user_profiles = factory.Sequence(lambda n: n)
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


class DataCatalogueMetaDataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DataCatalogueMetaData

    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
    if is_fares_validator_active:
        acto_area = factory.Sequence(lambda n: n)
        valid_from = datetime.datetime(2000, 5, 7)
        valid_to = datetime.datetime(2099, 5, 7)
        line_id = factory.Sequence(lambda n: n)
        line_name = factory.Sequence(lambda n: n)
        national_operator_code = factory.Sequence(lambda n: n)
        product_name = factory.Sequence(lambda n: n)
        product_type = factory.Sequence(lambda n: n)
        tariff_basis = factory.Sequence(lambda n: n)
        user_type = factory.Sequence(lambda n: n)
        xml_file_name = factory.Sequence(lambda n: n)
