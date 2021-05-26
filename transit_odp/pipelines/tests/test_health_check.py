import pytest
from django.conf import settings

from transit_odp.common.enums import FeedErrorCategory, FeedErrorSeverity
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.organisation.models import Dataset
from transit_odp.pipelines.factories import (
    DatasetETLErrorFactory,
    RemoteDatasetHealthCheckCountFactory,
)
from transit_odp.pipelines.pipelines.health_check.main import (
    handle_feed_available,
    handle_feed_unavailable,
    monitor_available_feeds,
    monitor_feed,
    monitor_feeds,
    reindex_feed,
    retry_unavailable_feeds,
)

pytestmark = pytest.mark.django_db


class TestMonitorFeeds:
    # module-under-test
    mut = "transit_odp.pipelines.pipelines.health_check.main"

    # monitor_available_feeds

    def test_monitor_available_feeds_filters_feeds_with_no_retries(self, mocker):
        """Tests monitor_available_feeds only selects feeds with no failed monitoring
        attempts"""
        # Setup
        # Create two feeds as we want to test what happens if one doesn't have
        # availability_retry_count related object
        revisions = DatasetRevisionFactory.create_batch(
            2,
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.success.value,
        )

        # Only one feed has a counter, the other should implicitly have count zero
        RemoteDatasetHealthCheckCountFactory(revision=revisions[0])

        # create revision with a retry attempts
        unavailable_revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.success.value,
        )
        RemoteDatasetHealthCheckCountFactory(revision=unavailable_revision, count=1)

        # mock out monitor_feeds
        mocked = mocker.patch(f"{self.mut}.monitor_feeds", return_value=None)

        # Test
        monitor_available_feeds()

        # Assert
        # expected doesn't include unavailable feed
        args, _ = mocked.call_args
        assert set(feed.id for feed in args[0]) == {
            revision.dataset.id for revision in revisions
        }

    # retry_unavailable_feeds

    def test_retry_unavailable_feeds_filters_feeds_with_retries(self, mocker):
        """Tests retry_unavailable_feeds only selects feeds with failed
        monitoring attempts"""
        # Setup
        # Create two feeds as we want to test what happens if one doesn't
        # have availability_retry_count related object
        revisions = DatasetRevisionFactory.create_batch(
            2,
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.success.value,
        )

        # Only one feed has a counter, the other should implicitly have count zero
        RemoteDatasetHealthCheckCountFactory(revision=revisions[0])

        # create feed with a retry attempts
        unavailable_revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.success.value,
        )
        RemoteDatasetHealthCheckCountFactory(revision=unavailable_revision, count=1)

        # mock out monitor_feeds
        mocked = mocker.patch(f"{self.mut}.monitor_feeds", return_value=None)

        # Test
        retry_unavailable_feeds()

        # Assert
        args, _ = mocked.call_args
        assert set(dataset.id for dataset in args[0]) == {
            unavailable_revision.dataset.id
        }

    # monitor_feeds

    def test_monitor_feeds(self, mocker):
        """Tests published, live, remote feeds are monitored"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.success.value,
        )
        # create local/expired datasets for negative test
        DatasetRevisionFactory(is_published=True, status=FeedStatus.success.value)
        DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.expired.value,
        )

        # mock out monitor_feed()
        mocked = mocker.patch(f"{self.mut}.monitor_feed", return_value=None)

        # Test
        monitor_feeds(Dataset.objects.all())

        # Assert
        mocked.assert_called_once_with(revision.dataset)

    # monitor_feed

    def test_monitor_feed_calls_handle_feed_available_when_ok(self, mocker):
        """Tests handle_feed_available is called if dataset available"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.success.value,
        )
        dataset = revision.dataset

        # mock out data response
        fetch_data = mocker.patch(f"{self.mut}.fetch_data", return_value=b"abcd")

        # mock out handler
        mocked_handler = mocker.patch(
            f"{self.mut}.handle_feed_available", return_value=None
        )

        # Test
        monitor_feed(dataset)

        # Assert
        fetch_data.assert_called_once_with(revision.url_link)
        mocked_handler.assert_called_once_with(dataset, b"abcd")

    def test_monitor_feed__handle_feed_unavailable_when_not_ok(self, mocker):
        """Tests handle_feed_unavailable is called if dataset unavailable"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.live.value,
        )

        # mock out response
        # mock out data response
        fetch_data = mocker.patch(f"{self.mut}.fetch_data", return_value=None)

        # mock out handler
        mocked_handler = mocker.patch(
            f"{self.mut}.handle_feed_unavailable", return_value=None
        )

        dataset = revision.dataset

        # Test
        monitor_feed(dataset)

        # Assert
        fetch_data.assert_called_once_with(revision.url_link)
        mocked_handler.assert_called_once_with(dataset)

    # _handle_feed_available

    def test_availability_retry_count_reset(self, mocker):
        """Tests DatasetAvailabilityRetryCount is reset to zero if dataset available"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.live.value,
        )

        dataset = revision.dataset

        # create counter with a count of 1
        reset_counter = RemoteDatasetHealthCheckCountFactory(revision=revision, count=1)

        # mock out signals
        mocked_signal = mocker.patch(
            f"{self.mut}.signals.feed_monitor_dataset_available"
        )

        # mock out feed methods
        mocker.patch.object(
            dataset, "get_hash", return_value=dataset.compute_hash(b"abcd")
        )

        # Test
        handle_feed_available(dataset, b"abcd")

        # Assert
        assert reset_counter.count == 0
        mocked_signal.send.assert_called_once_with(None, dataset=dataset)

    def test_monitor_calls_index_if_changes_detected(self, mocker):
        """Tests monitor_feed calls feed.index() if change detected"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.live.value,
        )
        dataset = revision.dataset

        # mock out feed methods
        mocker.patch.object(
            dataset, "get_hash", return_value=dataset.compute_hash(b"wxyz")
        )
        mocker.patch.object(
            dataset, "get_file_content", return_value=b"wxyz"
        )  # TODO remove this patch, only needed to stub out debug statement

        # mock out manager method
        mocked_reindex = mocker.patch(f"{self.mut}.reindex_feed", return_value=None)

        # Test
        handle_feed_available(dataset, b"abcd")

        # Assert
        mocked_reindex.assert_called_once_with(dataset)

    # _handle_feed_unavailable

    def test_availability_retry_count_incremented_if_unavailable(self, mocker):
        """Tests DatasetAvailabilityRetryCount is incremented if dataset is
        unavailable"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.live.value,
        )
        dataset = revision.dataset

        # create counter
        reset_counter = RemoteDatasetHealthCheckCountFactory(revision=revision)

        # Test
        handle_feed_unavailable(dataset)

        # Assert
        assert reset_counter.count == 1

    def test_signal_sent_on_first_try(self, mocker):
        """Tests feed_monitor_fail_first_try is sent on first try"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.live.value,
        )
        dataset = revision.dataset

        # create counter
        RemoteDatasetHealthCheckCountFactory(revision=revision, count=0)

        # mock out signals
        mocked_signal = mocker.patch(f"{self.mut}.signals.feed_monitor_fail_first_try")

        # Test
        handle_feed_unavailable(dataset)

        # Assert
        mocked_signal.send.assert_called_once_with(None, dataset=dataset)

    def test_feed_expires_after_x_retries(self, mocker):
        """Tests feed status is set to expired after x number of retries"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.live.value,
        )
        dataset = revision.dataset

        # create counter
        reset_counter = RemoteDatasetHealthCheckCountFactory(
            revision=revision, count=settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS - 1
        )

        # mock out signals
        mocked_feed_monitor_fail_final_try = mocker.patch(
            f"{self.mut}.signals.feed_monitor_fail_final_try"
        )
        mocked_feed_expired = mocker.patch(f"{self.mut}.signals.feed_expired")

        # Test
        handle_feed_unavailable(dataset)

        # Assert
        assert reset_counter.count == settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS
        assert revision.status == FeedStatus.expired.value
        mocked_feed_monitor_fail_final_try.send.assert_called_once_with(
            None, dataset=dataset
        )
        mocked_feed_expired.send.assert_called_once_with(None, dataset=dataset)

    def test_feed_expires_with_errors(self, mocker):
        """Tests feed error is initialised with availability error when feed expires"""
        # Setup
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=True,
            status=FeedStatus.live.value,
        )
        dataset = revision.dataset

        # create some existing non-severe errors
        DatasetETLErrorFactory.create_batch(
            2, revision=revision, severity=FeedErrorSeverity.minor.value
        )

        # create counter
        RemoteDatasetHealthCheckCountFactory(revision=revision, count=5)

        # mock out signals
        mocker.patch(f"{self.mut}.signals.feed_monitor_fail_final_try")
        mocker.patch(f"{self.mut}.signals.feed_expired")

        # Test
        handle_feed_unavailable(dataset)

        # Assert
        assert revision.status == FeedStatus.expired.value

        errors = revision.errors.all()
        assert len(errors) == 1

        error = errors[0]
        assert error.severity == FeedErrorSeverity.severe.value
        assert error.category == FeedErrorCategory.availability.value
        assert error.description == "Data set is not reachable"

    def test_reindex_feed(self, mocker):
        """Tests reindex_feed creates a new revision and triggers etl"""
        # Setup
        dataset = mocker.Mock()
        revision = dataset.start_revision.return_value

        # mock out signals
        mocked_dataset_changed = mocker.patch(f"{self.mut}.dataset_changed")

        # Test
        reindex_feed(dataset)

        # Assert
        dataset.start_revision.assert_called_once_with(
            comment="Automatically detected change in data set"
        )
        revision.save.assert_called_once()
        mocked_dataset_changed.send.assert_called_once_with(None, revision=revision)
