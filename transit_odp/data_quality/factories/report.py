import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from transit_odp.data_quality.models.report import PTIObservation
from transit_odp.organisation.factories import DatasetRevisionFactory


class PTIObservationFactory(DjangoModelFactory):
    class Meta:
        model = PTIObservation

    revision = factory.SubFactory(DatasetRevisionFactory)
    filename = "file.xml"
    line = 1
    details = "This should not be happening."
    element = "Element"
    category = "Accessibility Information"
    reference = "2.4.3"
    created = factory.LazyFunction(timezone.now)
