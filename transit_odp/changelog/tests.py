import datetime

import pytest
from django.utils import timezone
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import ROOT_HOST
from transit_odp.changelog.constants import ConsumerIssue, PublisherIssue
from transit_odp.changelog.factories import KnownIssueFactory
from transit_odp.changelog.models import HighLevelRoadMap, KnownIssues

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


def test_last_modified_updates_when_deleting_issue(client_factory):
    now = timezone.now()
    with freeze_time("25-12-20"):
        KnownIssueFactory.create_batch(2, category=ConsumerIssue)
        KnownIssueFactory.create_batch(3, category=PublisherIssue, deleted=True)
        KnownIssueFactory.create_batch(5, category=PublisherIssue)

    with freeze_time(now):
        issue = KnownIssues.objects.first()
        issue.deleted = True
        issue.save()

    url = reverse("changelog", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)

    assert response.status_code == 200
    assert response.context["last_updated"] == now


def test_last_modified_is_defined_without_known_issues(client_factory):
    url = reverse("changelog", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)

    response = client.get(url)

    assert response.status_code == 200
    assert isinstance(response.context["last_updated"], datetime.datetime)


def test_last_modified_is_updated_when_roadmap_is_updated(client_factory):
    url = reverse("changelog", host=ROOT_HOST)
    client = client_factory(host=ROOT_HOST)
    now = timezone.now()

    with freeze_time("25-12-20"):
        KnownIssueFactory.create_batch(2, category=ConsumerIssue)
        KnownIssueFactory.create_batch(3, category=PublisherIssue, deleted=True)
        KnownIssueFactory.create_batch(5, category=PublisherIssue)

    with freeze_time(now):
        roadmap = HighLevelRoadMap.objects.first()
        roadmap.description = "this has been changed"
        roadmap.save()

    response = client.get(url)
    assert response.status_code == 200
    assert response.context["last_updated"] == now
