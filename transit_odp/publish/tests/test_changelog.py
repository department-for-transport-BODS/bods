from datetime import datetime

import pytest
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.pipelines.factories import DataQualityTaskFactory
from transit_odp.pipelines.models import TaskResult
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestChangelog:
    host = PUBLISH_HOST

    def setup(self):
        self.org = OrganisationFactory()
        self.user = UserFactory(
            account_type=AccountType.org_staff.value, organisations=(self.org,)
        )
        self.dataset = DatasetFactory(
            organisation=self.org, live_revision=None, contact=self.user
        )
        self.revision = DatasetRevisionFactory(
            status=FeedStatus.live.value,
            is_published=True,
            dataset=self.dataset,
        )
        self.url = reverse(
            "feed-changelog",
            host=self.host,
            kwargs={"pk": self.dataset.id, "pk1": self.org.id},
        )

    def test_dataquality_column_with_successful_report(self, client_factory):
        report = DataQualityReportFactory(revision=self.revision)
        DataQualityTaskFactory(
            revision=self.revision, status=TaskResult.SUCCESS, report=report
        )

        client = client_factory(host=self.host)
        client.force_login(user=self.user)

        response = client.get(self.url)
        table = response.context["table"]
        cell = list(table.as_values(["comment", "status", "published_at"]))[1][0]
        assert "GREEN" in cell

    def test_dataquality_column_with_failed_report_task(self, client_factory):
        DataQualityTaskFactory(revision=self.revision, status=TaskResult.FAILURE)

        client = client_factory(host=self.host)
        client.force_login(user=self.user)

        response = client.get(self.url)
        table = response.context["table"]
        cell = list(table.as_values(["comment", "status", "published_at"]))[1][0]
        assert "Not available" in cell

    def test_dataquality_column_with_no_report_task(self, client_factory):
        client = client_factory(host=self.host)
        client.force_login(user=self.user)

        response = client.get(self.url)
        table = response.context["table"]
        cell = list(table.as_values(["comment", "status", "published_at"]))[1][0]
        assert "Not available" in cell

    def test_dataquality_column_with_hanging_report_task(self, client_factory):
        task = DataQualityTaskFactory(
            revision=self.revision,
            status=TaskResult.STARTED,
        )
        # I have no idea why we cant just put the created date in the init kwargs
        # like we can for revision.
        task.created = datetime(2019, 12, 25, 23, 59, 0)
        task.save()

        client = client_factory(host=self.host)
        client.force_login(user=self.user)

        response = client.get(self.url)
        table = response.context["table"]
        cell = list(table.as_values(["comment", "status", "published_at"]))[1][0]
        assert "Not available" in cell

    def test_dataquality_column_with_new_task(self, client_factory):
        DataQualityTaskFactory(revision=self.revision, status=TaskResult.STARTED)

        client = client_factory(host=self.host)
        client.force_login(user=self.user)

        response = client.get(self.url)
        table = response.context["table"]
        cell = list(table.as_values(["comment", "status", "published_at"]))[1][0]
        assert "Generating" in cell
