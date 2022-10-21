import factory
from django.utils import timezone

from transit_odp.common.enums import FeedErrorCategory, FeedErrorSeverity
from transit_odp.common.utils import sha1sum
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.models import (
    BulkDataArchive,
    ChangeDataArchive,
    DataQualityTask,
    DatasetETLError,
    DatasetETLTaskResult,
    RemoteDatasetHealthCheckCount,
    SchemaDefinition,
    TaskResult,
)


class RemoteDatasetHealthCheckCountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RemoteDatasetHealthCheckCount

    revision = factory.SubFactory(DatasetRevisionFactory)


class DatasetETLErrorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DatasetETLError

    revision = factory.SubFactory(DatasetRevisionFactory)
    severity = FeedErrorSeverity.severe.value
    category = FeedErrorCategory.unknown.value
    description = factory.Faker("paragraph")


class DatasetETLTaskResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DatasetETLTaskResult

    revision = factory.SubFactory(DatasetRevisionFactory)
    task_id = factory.Sequence(lambda n: f"task_{n}")
    progress = 0


class BulkDataArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BulkDataArchive

    created = factory.LazyFunction(timezone.now)
    data = factory.django.FileField(filename="bulk_archive.zip")
    traveline_regions = "All"
    compliant_archive = False
    dataset_type = TimetableType


class ChangeDataArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChangeDataArchive

    published_at = factory.LazyFunction(lambda: timezone.now().date())
    data = factory.django.FileField(filename="change_archive.zip")


class TaskResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TaskResult

    task_id = factory.Sequence(lambda n: f"task_{n}")
    status = TaskResult.PENDING


class DataQualityTaskFactory(TaskResultFactory):
    class Meta:
        model = DataQualityTask

    revision = factory.SubFactory(DatasetRevisionFactory)
    task_id = factory.Faker("uuid4")


class SchemaDefinitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SchemaDefinition

    category = "TxC"
    schema = factory.django.FileField(
        filename="TransXChange_schema_2.4.zip", data=b"old data"
    )

    @factory.lazy_attribute
    def checksum(self):
        return sha1sum(self.schema.read())
