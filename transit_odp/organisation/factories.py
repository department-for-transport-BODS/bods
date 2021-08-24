import datetime
from typing import List, Union

import factory
import faker
import pytz
from django.utils import timezone
from factory.django import DjangoModelFactory
from freezegun import freeze_time

from transit_odp.organisation.constants import (
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.models import (
    Dataset,
    DatasetMetadata,
    DatasetRevision,
    DatasetSubscription,
    Licence,
    OperatorCode,
    Organisation,
    TXCFileAttributes,
)

FAKER = faker.Faker()


class OrganisationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organisation

    short_name = factory.Faker("company")
    name = factory.Sequence(lambda n: factory.Faker("company").generate() + f" {n}")
    key_contact = None
    is_active = True
    licence_required = None

    @factory.post_generation
    def nocs(obj, create, extracted: Union[int, List[str]] = None, **kwargs):
        """
        Examples:
            1. OrganisationFactory(nocs=['X', 'Y', 'Z']) => creates three NOCs
            2. OrganisationFactory() => creates a random NOC
            3. OrganisationFactory(nocs=4)  => creates four random NOCs
        """
        if not create:
            # Build, not create related
            return

        if extracted is None:
            # Create one random NOC
            OperatorCodeFactory(organisation=obj)
        elif isinstance(extracted, int):
            # Create list of random NOCs
            for i in range(extracted):
                OperatorCodeFactory(organisation=obj)
        elif isinstance(extracted, list):
            # Create list of NOCs from args
            for noc in extracted:
                OperatorCodeFactory(organisation=obj, noc=noc)


class OperatorCodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OperatorCode

    noc = factory.Sequence(lambda n: "NOC %03d" % n)
    organisation = factory.SubFactory(OrganisationFactory)


class LicenceFactory(DjangoModelFactory):
    class Meta:
        model = Licence

    number = factory.Sequence(lambda n: f"PD0000{n:03}")
    organisation = factory.SubFactory(OrganisationFactory)


class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dataset

    organisation = factory.SubFactory(OrganisationFactory)
    contact = factory.SubFactory("transit_odp.users.factories.UserFactory")
    dataset_type = TimetableType
    # Even though live_revision is a OneToOneField, RelatedFactory gives us the
    # ability to set the dataset FK on the generated DatasetRevision back to the
    # parent Dataset
    live_revision = factory.RelatedFactory(
        "transit_odp.organisation.factories.DatasetRevisionFactory", "dataset"
    )

    @factory.post_generation
    def subscribers(self, create, extracted, **kwargs):
        if not create:
            return None
        if extracted:
            for subscriber in extracted:
                DatasetSubscriptionFactory.create(dataset=self, user=subscriber)


class DraftDatasetFactory(DatasetFactory):
    live_revision = None
    revision = factory.RelatedFactory(
        "transit_odp.organisation.factories.DatasetRevisionFactory",
        "dataset",
        is_published=False,
        status=FeedStatus.draft.value,
    )

    class Meta:
        exclude = ("revision",)


class DatasetRevisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DatasetRevision

    # live_revision is automatically by a post-save signal
    dataset = factory.SubFactory(DatasetFactory, live_revision=None)
    name = factory.Sequence(lambda n: factory.Faker("sentence").generate() + f" {n}")
    description = factory.Faker("paragraph")
    short_description = factory.Faker("pystr", min_chars=1, max_chars=30)
    comment = factory.Faker("paragraph")
    status = FeedStatus.live.value
    is_published = True
    transxchange_version = 2.4
    published_at = factory.LazyAttribute(
        lambda obj: timezone.now() if (obj.is_published or obj.published_by) else None
    )
    published_by = None

    first_service_start = datetime.datetime(2019, 5, 7, tzinfo=pytz.utc)
    upload_file = factory.django.FileField(filename="transXchange.xml")

    @classmethod
    def create(cls, created=None, **kwargs):
        if created is not None:
            with freeze_time(created):
                return super().create(**kwargs)
        else:
            return super().create(**kwargs)

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

    @factory.post_generation
    def task_progress(self, create, extracted, **kwargs):
        from transit_odp.pipelines.factories import DatasetETLTaskResultFactory

        if not create:
            # simple build, do nothing
            return
        if extracted:
            # A list of groups were passed in, use them
            for progress in extracted:
                DatasetETLTaskResultFactory.create(revision=self, task_result=progress)


class AVLDatasetRevisionFactory(DatasetRevisionFactory):
    dataset = factory.SubFactory(
        DatasetFactory, live_revision=None, dataset_type=AVLType
    )
    url_link = factory.Faker("url")
    upload_file = None
    first_service_start = None


class FaresDatasetRevisionFactory(DatasetRevisionFactory):
    dataset = factory.SubFactory(
        DatasetFactory, live_revision=None, dataset_type=FaresType
    )
    url_link = factory.Faker("url")
    upload_file = None
    first_service_start = None


class DatasetSubscriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DatasetSubscription

    user = factory.SubFactory("transit_odp.users.factories.UserFactory")
    dataset = factory.SubFactory(DatasetFactory)


class DatasetMetadataFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DatasetMetadata

    revision = factory.SubFactory(DatasetRevisionFactory)
    schema_version = "0.0"


class TXCFileAttributesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TXCFileAttributes

    revision = factory.SubFactory(DatasetRevisionFactory)
    modification = "new"
    schema_version = "2.4"
    revision_number = "0"
    modification = "new"
    filename = FAKER.file_name(extension="xml")
    service_code = FAKER.pystr(min_chars=4, max_chars=4)
    creation_datetime = FAKER.date_time(tzinfo=pytz.utc)
    modification_datetime = FAKER.date_time(tzinfo=pytz.utc)
    national_operator_code = "".join(FAKER.random_letters(length=4)).upper()
    licence_number = "PF0002280"
    operating_period_start_date = FAKER.date()
    operating_period_end_date = FAKER.date()
    public_use = True
    line_names = ["line1", "line2"]
