import factory
from factory.django import DjangoModelFactory
from transit_odp.organisation.factories import TXCFileAttributesFactory
from transit_odp.dqs.models import Checks, TaskResults, ObservationResults
from transit_odp.dqs.constants import TaskResultsStatus
from factory.fuzzy import FuzzyText
from transit_odp.transmodel.factories import ServicePatternStopFactory


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

    status = factory.Iterator([TaskResultsStatus["PENDING"], "completed"])
    message = factory.Faker("sentence")
    checks = factory.SubFactory(ChecksFactory)
    transmodel_txcfileattributes = factory.SubFactory(TXCFileAttributesFactory)
    dataquality_report = None


class ObservationResultsFactory(DjangoModelFactory):
    class Meta:
        model = ObservationResults

    details = FuzzyText(length=12)
    is_suppressed = False
    service_pattern_stop = factory.SubFactory(ServicePatternStopFactory)
    taskresults = factory.SubFactory(TaskResultsFactory)
