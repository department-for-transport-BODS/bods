import factory

from transit_odp.changelog.constants import ConsumerIssue, PendingStatus
from transit_odp.changelog.models import KnownIssues


class KnownIssueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = KnownIssues

    deleted = False
    status = PendingStatus
    category = ConsumerIssue
    description = factory.Faker("paragraph")
