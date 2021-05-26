from datetime import datetime, timedelta

from factory import DjangoModelFactory, Sequence, SubFactory, post_generation
from faker import Faker

from transit_odp.site_admin.models import APIRequest, OperationalStats
from transit_odp.users.factories import UserFactory

fake = Faker()


class OperationalStatsFactory(DjangoModelFactory):
    date = Sequence(lambda n: datetime(2020, 1, 1) + timedelta(days=n))
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
        """ `created` field is auto_now_add field so needs to be manually changed."""
        if not create:
            return None

        created = extracted or obj.created
        obj.created = created
        obj.save()
        return created

    class Meta:
        model = APIRequest
