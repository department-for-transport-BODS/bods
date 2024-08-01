import factory
from factory.django import DjangoModelFactory
from transit_odp.organisation.factories import TXCFileAttributesFactory
from transit_odp.dqs.models import Checks, TaskResults
from transit_odp.dqs.constants import STATUSES


class ChecksFactory(DjangoModelFactory):
    class Meta:
        model = Checks

    observation = "Sample observation"
    importance = "Medium"
    category = "Sample category"
    queue_name = factory.Faker("word")


class TaskResultsFactory(DjangoModelFactory):
    class Meta:
        model = TaskResults

    status = factory.Iterator([STATUSES["PENDING"], "completed"])
    message = factory.Faker("sentence")
    checks = factory.SubFactory(ChecksFactory)
    transmodel_txcfileattributes = factory.SubFactory(TXCFileAttributesFactory)
    dataquality_report = None
