import pytest
from django_hosts import reverse

from config.hosts import ROOT_HOST
from transit_odp.changelog.constants import (
    ConsumerIssue,
    FixedStatus,
    PublisherIssue,
)
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


def test_known_issues_api_is_public_and_hides_deleted_issues(client_factory):
    KnownIssueFactory.create_batch(2, category=PublisherIssue)
    KnownIssueFactory.create_batch(3, category=PublisherIssue, deleted=True)
    KnownIssueFactory.create(category=ConsumerIssue, status=FixedStatus)

    url = reverse("nextjs-changelog-known-issues", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)

    assert response.status_code == 200
    body = response.json()
    assert len(body[PublisherIssue]) == 2
    assert len(body[ConsumerIssue]) == 1
    assert set(body[ConsumerIssue][0]) == {"description", "status", "modified"}
    assert body[ConsumerIssue][0]["status"] == FixedStatus


def test_known_issues_api_orders_by_most_recently_modified(client_factory):
    older, newer = KnownIssueFactory.create_batch(2, category=PublisherIssue)
    older.description = "Most recently modified"
    older.save()

    url = reverse("nextjs-changelog-known-issues", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)

    descriptions = [issue["description"] for issue in response.json()[PublisherIssue]]
    assert descriptions == ["Most recently modified", newer.description]


def test_known_issues_api_returns_empty_sections(client_factory):
    url = reverse("nextjs-changelog-known-issues", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)

    assert response.json() == {PublisherIssue: [], ConsumerIssue: []}


def test_roadmap_section(client_factory):
    HighLevelRoadMapFactory.create_batch(1)

    url = reverse("changelog", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)
    assert response.status_code == 200
    roadmap = response.context["roadmap"]
    assert roadmap.description == "Coming soon"
