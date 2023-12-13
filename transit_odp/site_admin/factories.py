from datetime import datetime, timedelta

import factory
from dateutil.relativedelta import relativedelta
from factory import Sequence, SubFactory, post_generation
from faker import Faker

from transit_odp.site_admin.models import (
    APIRequest,
    MetricsArchive,
    OperationalStats,
    ResourceRequestCounter,
)
from transit_odp.users.factories import UserFactory
from factory.django import DjangoModelFactory

fake = Faker()


class OperationalStatsFactory(DjangoModelFactory):
    date = Sequence(lambda n: datetime(2020, 1, 1) + timedelta(days=n))
    registered_service_code_count = fake.random_digit()
    unregistered_service_code_count = fake.random_digit()
    vehicle_count = fake.random_digit()
    operator_count = fake.random_digit()
    operator_user_count = fake.random_digit()
    agent_user_count = fake.random_digit()
    consumer_count = fake.random_digit()
    timetables_count = fake.random_digit()
    avl_count = fake.random_digit()
    fares_count = fake.random_digit()
    published_timetable_operator_count = fake.random_digit()
    published_avl_operator_count = fake.random_digit()
    published_fares_operator_count = fake.random_digit()

    class Meta:
        model = OperationalStats


class APIRequestFactory(DjangoModelFactory):
    requestor = SubFactory(UserFactory)
    path_info = "/api/v1/dataset/"
    query_string = ""

    @post_generation
    def created(obj, create, extracted, **kwargs):
        """`created` field is auto_now_add field so needs to be manually changed."""
        if not create:
            return None

        created = extracted or obj.created
        obj.created = created
        obj.save()
        return created

    class Meta:
        model = APIRequest


class MetricsArchiveFactory(DjangoModelFactory):
    start = datetime.now().replace(day=1).date()
    end = datetime.now().replace(day=1).date() + relativedelta(day=31)
    archive = factory.django.FileField(filename="metrics_archive.zip")

    class Meta:
        model = MetricsArchive


class ResourceRequestCounterFactory(DjangoModelFactory):
    date = factory.LazyFunction(datetime.now)
    requestor = SubFactory(UserFactory)
    path_info = "/timetable/download/bulk_archive"
    counter = 1

    class Meta:
        model = ResourceRequestCounter
