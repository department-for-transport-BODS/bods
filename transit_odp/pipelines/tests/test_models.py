from datetime import datetime

import pytest

from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.factories import (
    DataQualityTaskFactory,
    DatasetETLTaskResultFactory,
    RemoteDatasetHealthCheckCountFactory,
)
from transit_odp.pipelines.models import DataQualityTask
from transit_odp.users.factories import AgentUserFactory

pytestmark = pytest.mark.django_db


MUT = "transit_odp.pipelines.models"


class TestRemoteDatasetHealthCheckCountFactory:
    def test_reset(self):
        """Tests count is reset to zero"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=False,
            status=FeedStatus.indexing.value,
        )
        reset_counter = RemoteDatasetHealthCheckCountFactory(revision=revision, count=1)

        # Test
        reset_counter.reset()

        # Assert
        assert reset_counter.count == 0


class TestDataQualityTask:
    def test_success(self, mocker):
        task = DataQualityTaskFactory()
        task.success(message="Done")
        assert task.status == DataQualityTask.SUCCESS

    def test_failure(self):
        # Setup
        task = DataQualityTaskFactory()

        # Test
        task.failure(message="Fail!")

        # Assert
        assert task.status == DataQualityTask.FAILURE

    def test_started(self):
        # Setup
        task = DataQualityTaskFactory()

        # Test
        task.started(message="Task started")

        # Assert
        assert task.status == DataQualityTask.STARTED


class TestDatasetETLTaskResult:
    def test_send_error_notification_when_revision_is_published(self, mailoutbox):
        indexing_revision = DatasetRevisionFactory(
            short_description="Indexing Revision",
            status=FeedStatus.indexing.value,
            is_published=False,
        )
        live_revision = DatasetRevisionFactory(
            short_description="Published Revision",
            status=FeedStatus.live.value,
            is_published=True,
            dataset=indexing_revision.dataset,
            created=datetime(2021, 4, 10, 16, 0, 4),
        )

        assert indexing_revision.dataset.live_revision == live_revision
        task = DatasetETLTaskResultFactory(revision=indexing_revision)
        task.to_error("dataset_validate", 101)
        mail = mailoutbox[0]

        assert mail.subject == "[BODS] Error publishing data set"
        assert "Indexing Revision" in mail.body
        assert f"Link to data set: {indexing_revision.draft_url}" in mail.body
        # Defends against: https://itoworld.atlassian.net/browse/BODP-3721
        assert "Published: Not published" not in mail.body

    def test_send_error_notification_when_revision_is_not_published(self, mailoutbox):
        indexing_revision = DatasetRevisionFactory(
            short_description="Indexing Revision",
            is_published=False,
            status=FeedStatus.indexing.value,
        )
        task = DatasetETLTaskResultFactory(revision=indexing_revision)
        task.to_error("dataset_validate", 101)
        mail = mailoutbox[0]

        assert mail.subject == "[BODS] Error publishing data set"
        assert "Indexing Revision" in mail.body
        assert "Published: Not published" in mail.body
        assert f"Link to data set: {indexing_revision.draft_url}" in mail.body
        # Defends against: https://itoworld.atlassian.net/browse/BODP-3721

    def test_agent_email_is_sent_on_error(self, mailoutbox):
        agent = AgentUserFactory()
        org = agent.organisations.first()
        indexing_revision = DatasetRevisionFactory(
            short_description="Indexing Revision",
            status=FeedStatus.indexing.value,
            is_published=False,
            dataset__contact=agent,
            dataset__organisation=org,
        )
        live_revision = DatasetRevisionFactory(
            short_description="Published Revision",
            status=FeedStatus.live.value,
            is_published=True,
            dataset=indexing_revision.dataset,
            created=datetime(2021, 4, 10, 16, 0, 4),
        )

        assert indexing_revision.dataset.live_revision == live_revision
        task = DatasetETLTaskResultFactory(revision=indexing_revision)
        task.to_error("dataset_validate", 101)
        mail = mailoutbox[0]

        assert mail.subject == "[BODS] Error publishing data set"
        assert f"Operator: {org.name}" in mail.body
