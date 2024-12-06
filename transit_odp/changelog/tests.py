import pytest
from django_hosts import reverse

from config.hosts import ROOT_HOST
from transit_odp.changelog.constants import ConsumerIssue, PublisherIssue
from transit_odp.changelog.factories import HighLevelRoadMapFactory, KnownIssueFactory

pytestmark = pytest.mark.django_db


def test_correct_number_of_consumer_issues_are_returned(client_factory):
    KnownIssueFactory.create_batch(2, category=PublisherIssue)
    KnownIssueFactory.create_batch(3, category=ConsumerIssue, deleted=True)
    KnownIssueFactory.create_batch(5, category=ConsumerIssue)

    url = reverse("changelog", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)

    assert response.status_code == 200
    fetched_issues = response.context["known_issues"]

    assert len(fetched_issues[ConsumerIssue]) == 5


def test_correct_number_of_publisher_issues_are_returned(client_factory):
    KnownIssueFactory.create_batch(2, category=ConsumerIssue)
    KnownIssueFactory.create_batch(3, category=PublisherIssue, deleted=True)
    KnownIssueFactory.create_batch(5, category=PublisherIssue)

    url = reverse("changelog", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)

    assert response.status_code == 200
    fetched_issues = response.context["known_issues"]

    assert len(fetched_issues[PublisherIssue]) == 5


def test_roadmap_section(client_factory):
    HighLevelRoadMapFactory.create_batch(1)

    url = reverse("changelog", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)
    assert response.status_code == 200
    roadmap = response.context["roadmap"]
    assert roadmap.description == "Coming soon"
