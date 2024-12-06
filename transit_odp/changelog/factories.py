import factory
from factory.django import DjangoModelFactory

from transit_odp.changelog.constants import ConsumerIssue, PendingStatus
from transit_odp.changelog.models import HighLevelRoadMap, KnownIssues


class KnownIssueFactory(DjangoModelFactory):
    class Meta:
        model = KnownIssues

    deleted = False
    status = PendingStatus
    category = ConsumerIssue
    description = factory.Faker("paragraph")


class HighLevelRoadMapFactory(DjangoModelFactory):
    class Meta:
        model = HighLevelRoadMap

    description = "Coming soon"
