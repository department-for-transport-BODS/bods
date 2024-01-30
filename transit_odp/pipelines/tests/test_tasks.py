from unittest.mock import Mock

import pytest

from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.organisation.models import DatasetRevision
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.tasks import task_run_naptan_etl
from transit_odp.timetables.tasks import task_dataset_etl, task_publish_revision
from transit_odp.users.constants import AccountType

pytestmark = pytest.mark.django_db

MUT = "transit_odp.pipelines.tasks"
TXC_PIPELINE = "transit_odp.timetables.tasks.TransXChangePipeline"


class TestTaskFeedIndex:
    def test_dataset_etl_called_correctly(self, mocker):
        revision = DatasetRevisionFactory()
        task = DatasetETLTaskResultFactory(revision=revision)
        pipeline = mocker.Mock()
        mocker.patch(TXC_PIPELINE, return_value=pipeline)

        task_dataset_etl(revision.id, task.id)

        pipeline.extract.assert_called_once()
        pipeline.transform.assert_called_once()
        pipeline.load.assert_called_once()
        task.refresh_from_db()
        assert task.progress == 90

    # TODO - notify feed published is no longer called on success
    @pytest.mark.skip
    def test_notify_feed_published_called_on_success(self, mocker):
        # Set up
        revision = DatasetRevisionFactory()

        MockedFeedParser: Mock = mocker.patch(f"{MUT}.FeedParser")

        # get mocked instance of MockedFeedParser
        mc = MockedFeedParser.return_value

        # We also need to mock out 'Feed.objects.get' so we can keep a
        # reference to the instance
        MockedFeed = mocker.Mock()
        mocker.patch(f"{MUT}.apps.get_model", return_value=MockedFeed)
        MockedFeed.objects.get.return_value = revision

        # add side effect to index_feed to set feed to live
        def _side_effect():
            revision.status = FeedStatus.success.value

        mc.index_feed.side_effect = _side_effect

        # mock out other functions not under test
        mocker.patch(f"{MUT}.notify_feed_error")
        mocker.patch(f"{MUT}.TaskResult")
        mocker.patch(f"{MUT}.DatasetETLTaskResult")

        # Test
        task_dataset_etl(revision.id)

        # Assert
        # mocked_notify.assert_called_once_with(revision)

    @pytest.mark.skip
    def test_notify_feed_error_called_on_error(self, mocker, mailoutbox, user_factory):
        # TODO - it would be better if the notifications were a explicit part of
        # the pipeline.
        # Set up
        user = user_factory(account_type=AccountType.org_staff.value)
        revision = DatasetRevisionFactory(last_modified_user=user)

        MockedFeedParser: Mock = mocker.patch(f"{MUT}.FeedParser")
        mc = MockedFeedParser.return_value

        # We also need to mock out 'Feed.objects.get' so we can keep a
        # reference to the instance
        MockedModel = mocker.patch(f"{MUT}.DatasetRevision")
        # TODO - refactor this into a function to make it easier to mock out
        MockedModel.objects.select_related.return_value.get.return_value = revision

        # add side effect to index_feed to set feed to error
        def _side_effect():
            revision.status = FeedStatus.error.value

        mc.index_feed.side_effect = _side_effect

        # mock out other functions not under test
        # mocker.patch(f"{target_module}.notify_feed_published")
        mocker.patch(f"{MUT}.TaskResult")
        mocker.patch(f"{MUT}.DatasetETLTaskResult")

        # Test
        task_dataset_etl(revision.id)

        # Assert
        assert mailoutbox[-1].subject == "Operator Publish Error"


class TestTaskPublishRevision:
    def test_task_revision_success(self, mocker):
        revision = DatasetRevisionFactory(status="success", is_published=False)
        task_publish_revision(revision.id)
        revision = DatasetRevision.objects.get(id=revision.id)
        assert revision.is_published is True
        assert revision.status == "live"

    def test_task_revision_error(self, mocker):
        revision = DatasetRevisionFactory(status="error", is_published=False)
        task_publish_revision(revision.id)
        revision = DatasetRevision.objects.get(id=revision.id)
        assert revision.is_published is True
        assert revision.status == "error"


class TestTaskNaptanETL:
    mut = "transit_odp.pipelines.tasks"

    def test_task_run_naptan_etl(self, mocker):
        mocked = mocker.patch(f"{self.mut}.main")
        task_run_naptan_etl()
        mocked.run.assert_called_once_with()
