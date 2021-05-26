from unittest.mock import Mock, patch

import pytest

from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import DatasetFactory
from transit_odp.timetables.exceptions import TransXChangeException
from transit_odp.timetables.updaters import TimetableUpdater

pytestmark = pytest.mark.django_db

UPDATERS_MODULE = "transit_odp.timetables.updaters."
FIRST_NOTIFICATION = UPDATERS_MODULE + "send_feed_monitor_fail_first_try_notification"
LAST_NOTIFICATION = UPDATERS_MODULE + "send_feed_monitor_fail_final_try_notification"
URL_AVAILABLE = UPDATERS_MODULE + "send_endpoint_available_notification"
REQUESTS = UPDATERS_MODULE + "requests"


class TestTimetableUpdater:
    def test_retry_count(self):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        updater = TimetableUpdater(dataset, mock_task)
        assert updater.retry_count == 0
        updater.retry_count += 1
        dataset.refresh_from_db()
        assert updater.retry_count == 1
        assert dataset.get_availability_retry_count().count == 1
        updater.reset_retry_count()
        dataset.refresh_from_db()
        assert updater.retry_count == 0
        assert dataset.get_availability_retry_count().count == 0

    def test_missing_url(self):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        updater = TimetableUpdater(dataset, mock_task)
        assert updater.url == ""
        with pytest.raises(TransXChangeException) as exc:
            updater._get_content("")
            expected_msg = f"Dataset {updater.pk} => Unable to check for new data."
            assert str(exc.value) == expected_msg

    @patch(FIRST_NOTIFICATION)
    def test_timetable_unavailable_first_try(self, send_notification):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        updater = TimetableUpdater(dataset, mock_task)

        updater.retry_count = 2
        updater._timetable_unavailable()
        send_notification.assert_not_called()
        assert updater._dataset.live_revision.status == "live"

        updater.reset_retry_count()
        updater._timetable_unavailable()
        send_notification.assert_called_once()
        assert updater._dataset.live_revision.status == "live"

    @patch(LAST_NOTIFICATION)
    def test_timetable_unavailable_final_try(self, send_notification):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        updater = TimetableUpdater(dataset, mock_task)

        updater.retry_count = 6
        updater._timetable_unavailable()
        send_notification.assert_called_once()
        assert updater._dataset.live_revision.status == "expired"

    @patch(URL_AVAILABLE)
    def test_url_available(self, send_notification):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        updater = TimetableUpdater(dataset, mock_task)
        updater.retry_count = 0

        updater._url_available()
        send_notification.assert_not_called()

        updater.retry_count = 1
        updater._url_available()
        send_notification.assert_called_once()
        assert updater.retry_count == 0

    def test_from_pk(self):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        updater = TimetableUpdater.from_pk(dataset.pk, mock_task)
        assert dataset == updater._dataset

    @patch(URL_AVAILABLE)
    @patch(REQUESTS)
    def test_has_been_updated(self, mock_requests, send_notification):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        mock_requests.get.return_value = Mock(content=b"<Updated Data>", ok=True)
        updater = TimetableUpdater(dataset, mock_task)

        has_updated = updater.has_new_update
        assert has_updated
        send_notification.assert_not_called()

    @patch(URL_AVAILABLE)
    @patch(REQUESTS)
    def test_has_not_been_updated(self, mock_requests, send_notification):
        dataset = DatasetFactory(dataset_type=TimetableType)
        mock_task = Mock()
        mock_requests.get.return_value = Mock(content=b"", ok=True)
        updater = TimetableUpdater(dataset, mock_task)

        has_updated = updater.has_new_update
        assert not has_updated
        send_notification.assert_not_called()
