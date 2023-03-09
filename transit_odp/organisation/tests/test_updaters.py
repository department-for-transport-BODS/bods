from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from requests.exceptions import ConnectTimeout

from transit_odp.organisation.constants import INACTIVE, TimetableType
from transit_odp.organisation.factories import DatasetFactory, DatasetRevisionFactory
from transit_odp.organisation.updaters import (
    ERROR,
    DatasetUpdateException,
    DatasetUpdater,
    update_dataset,
)

pytestmark = pytest.mark.django_db

UPDATERS_MODULE = "transit_odp.organisation.updaters."
FIRST_NOTIFICATION = UPDATERS_MODULE + "send_feed_monitor_fail_first_try_notification"
LAST_NOTIFICATION = UPDATERS_MODULE + "send_feed_monitor_fail_final_try_notification"
URL_AVAILABLE = UPDATERS_MODULE + "send_endpoint_available_notification"
REQUESTS = UPDATERS_MODULE + "requests"


def test_retry_count():
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    assert updater.retry_count == 0
    updater.retry_count += 1
    dataset.refresh_from_db()
    assert updater.retry_count == 1
    assert dataset.get_availability_retry_count().count == 1
    updater.reset_retry_count()
    dataset.refresh_from_db()
    assert updater.retry_count == 0
    assert dataset.get_availability_retry_count().count == 0


def test_missing_url():
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    assert updater.url == ""
    with pytest.raises(DatasetUpdateException) as exc:
        updater.get_content()
        expected_msg = f"Dataset {updater.pk} => Unable to check for new data."
        assert str(exc.value) == expected_msg


def test_deactivate_dataset():
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    assert dataset.live_revision.status == "live"
    updater.deactivate_dataset()
    dataset.refresh_from_db()
    assert dataset.live_revision.status == INACTIVE
    assert dataset.live_revision.comment == "Data set is not reachable"


def test_no_draft():
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    draft = updater.draft
    assert draft is None


def test_draft():
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    dataset.start_revision()
    draft = updater.draft
    assert draft is None


@patch(REQUESTS)
def test_get_content_success(requests):
    content = b"123"
    response = Mock(content=content, ok=True)
    requests.get.return_value = response
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    content = updater.get_content()
    assert content == content


@patch(REQUESTS)
def test_multiple_content_access(requests):
    content = b"123"
    response = Mock(content=content, ok=True)
    requests.get.return_value = response
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    assert updater.content == content
    assert updater.content == content
    requests.get.assert_called_once()


@patch(REQUESTS)
def test_get_content_unsuccessful(requests):
    response = Mock(content=b"", ok=False, status_code=404)
    requests.get.return_value = response
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    with pytest.raises(DatasetUpdateException) as exc:
        updater.get_content()
        expected_msg = f"Dataset {dataset.pk} => {updater.url} returned 404."
        assert str(exc.value) == expected_msg


@patch(REQUESTS)
def test_get_content_timeout(requests):
    requests.get.side_effect = ConnectTimeout()
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)
    with pytest.raises(DatasetUpdateException) as exc:
        updater.get_content()
        expected_msg = (
            f"Dataset {dataset.pk} => {updater.url} is currently unavailable."
        )
        assert str(exc.value) == expected_msg


def test_has_new_update_no_file():
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file=None
    )
    updater = DatasetUpdater(dataset)
    assert not updater.has_new_update()


@pytest.mark.parametrize(
    ("remote_content", "file_content", "expected"),
    [(b"123", b"123", False), (b"1", b"3", True)],
)
def test_has_new_update(remote_content, file_content, expected):
    response = Mock(content=remote_content, ok=True)
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    with patch(REQUESTS) as requests:
        requests.get.return_value = response
        updater = DatasetUpdater(dataset)
        assert updater.has_new_update() == expected


def test_start_new_revision_no_draft():
    dataset = DatasetFactory(dataset_type=TimetableType)
    updater = DatasetUpdater(dataset)

    assert dataset.revisions.get_draft().count() == 0
    revision = updater.start_new_revision()
    assert revision is not None


def test_start_new_revision_errored_draft():
    dataset = DatasetFactory(dataset_type=TimetableType)
    draft = DatasetRevisionFactory(dataset=dataset, is_published=False, status=ERROR)
    updater = DatasetUpdater(dataset)

    assert dataset.revisions.get_draft().count() == 1
    revision = updater.start_new_revision()
    dataset.refresh_from_db()
    assert dataset.revisions.get_draft().count() == 1
    assert revision != draft


def test_start_new_revision_do_nothing():
    dataset = DatasetFactory(dataset_type=TimetableType)
    DatasetRevisionFactory(dataset=dataset, is_published=False, status="success")
    updater = DatasetUpdater(dataset)

    assert dataset.revisions.get_draft().count() == 1
    revision = updater.start_new_revision()
    dataset.refresh_from_db()
    assert dataset.revisions.get_draft().count() == 1
    assert revision is None


def test_no_update_do_nothing():
    remote_content = b"1"
    file_content = b"1"
    response = Mock(content=remote_content, ok=True)
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    live_revision = dataset.live_revision
    assert dataset.revisions.get_draft().count() == 0
    with patch(REQUESTS) as requests:
        requests.get.return_value = response
        update_dataset(dataset, None)
    dataset.refresh_from_db()
    assert live_revision == dataset.live_revision
    assert dataset.revisions.get_draft().count() == 0


def test_update_but_good_draft_exists():
    remote_content = b"1"
    file_content = b"2"
    response = Mock(content=remote_content, ok=True)
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    draft = DatasetRevisionFactory(
        dataset=dataset, is_published=False, status="success"
    )

    live_revision = dataset.live_revision
    assert dataset.revisions.get_draft().count() == 1
    with patch(REQUESTS) as requests:
        requests.get.return_value = response
        update_dataset(dataset, None)
    dataset.refresh_from_db()
    assert live_revision == dataset.live_revision
    assert dataset.revisions.get_draft().count() == 1
    assert dataset.revisions.get_draft().first() == draft


@patch(URL_AVAILABLE)
def test_has_update_true_retry_is_one(endpoint_available):
    remote_content = b"1"
    file_content = b"2"
    response = Mock(content=remote_content, ok=True)
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    retry = dataset.get_availability_retry_count()
    retry.count = 1
    retry.save()

    live_revision = dataset.live_revision
    with patch(REQUESTS) as requests:
        requests.get.return_value = response
        update_dataset(dataset, None)
    dataset.refresh_from_db()
    assert live_revision == dataset.live_revision
    endpoint_available.assert_called_once()


@patch(FIRST_NOTIFICATION)
def test_unavailable_url_first_notification(first_notification):
    file_content = b"2"
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    task = Mock()
    before_draft_count = dataset.revisions.get_draft().count()
    with patch(REQUESTS) as requests:
        requests.get.side_effect = ConnectTimeout()
        update_dataset(dataset, task)

    dataset.refresh_from_db()
    assert dataset.revisions.get_draft().count() == before_draft_count
    assert dataset.get_availability_retry_count().count == 1
    first_notification.assert_called_once_with(dataset)


@patch(LAST_NOTIFICATION)
@patch(FIRST_NOTIFICATION)
def test_unavailable_url_second_notification(first_notification, last_notification):
    file_content = b"2"
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    task = Mock()
    retry = dataset.get_availability_retry_count()
    retry.count = 2
    retry.save()

    with patch(REQUESTS) as requests:
        requests.get.side_effect = ConnectTimeout()
        update_dataset(dataset, task)

    dataset.refresh_from_db()
    assert dataset.get_availability_retry_count().count == 3
    first_notification.assert_not_called()
    last_notification.assert_not_called()


@patch(LAST_NOTIFICATION)
@patch(FIRST_NOTIFICATION)
def test_unavailable_url_final_attempt(first_notification, last_notification):
    file_content = b"2"
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    task = Mock()
    retry = dataset.get_availability_retry_count()
    retry.count = settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS - 1
    retry.save()

    with patch(REQUESTS) as requests:
        requests.get.side_effect = ConnectTimeout()
        update_dataset(dataset, task)

    dataset.refresh_from_db()
    retries = dataset.get_availability_retry_count().count
    assert retries == settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS
    first_notification.assert_not_called()
    last_notification.assert_called_once_with(dataset)


@patch(URL_AVAILABLE)
def test_unavailable_url_ok_again(url_available_notification):
    file_content = b"2"
    dataset = DatasetFactory(
        dataset_type=TimetableType, live_revision__upload_file__data=file_content
    )
    task = Mock()
    retry = dataset.get_availability_retry_count()
    retry.count = 2
    retry.save()

    with patch(REQUESTS) as requests:
        requests.get.return_value = Mock(content=file_content, ok=True)
        update_dataset(dataset, task)

    dataset.refresh_from_db()
    retries = dataset.get_availability_retry_count().count
    assert retries == 0
    url_available_notification.assert_called_once_with(dataset)
