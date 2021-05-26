import datetime

import factory

from transit_odp.fares.models import FaresMetadata
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
