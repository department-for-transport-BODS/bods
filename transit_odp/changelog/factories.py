import factory

from transit_odp.changelog.constants import ConsumerIssue, PendingStatus
from transit_odp.changelog.models import KnownIssues
from factory.django import DjangoModelFactory

class KnownIssueFactory(DjangoModelFactory):
    class Meta:
        model = KnownIssues

    deleted = False
    status = PendingStatus
    category = ConsumerIssue
    description = factory.Faker("paragraph")
