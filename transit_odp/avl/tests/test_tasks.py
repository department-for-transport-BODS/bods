import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from requests import RequestException

from transit_odp.avl.factories import CAVLValidationTaskResultFactory
from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.avl.tasks import (
    task_create_sirivm_zipfile,
    task_monitor_avl_feeds,
    task_validate_avl_feed,
)
from transit_odp.bods.interfaces.gateways import AVLFeed
from transit_odp.organisation.constants import (
    AVLFeedDown,
    AVLFeedStatus,
    AVLFeedUp,
    AVLType,
    FeedStatus,
)
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetMetadataFactory,
    DatasetRevisionFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.users.constants import DeveloperType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db
CAVL_PATH = "transit_odp.avl.tasks.get_cavl_service"


@patch("transit_odp.avl.tasks.CAVLDataArchive")
@patch("transit_odp.avl.tasks.requests")
def test_task_create_sirivm_zipfile(mrequests, marchive):
    filter_ = marchive.objects.filter.return_value = MagicMock()
    filter_.last.return_value = None
    mresponse = MagicMock(content=b"hello")
    mrequests.get.return_value = mresponse
    task_create_sirivm_zipfile()
    marchive.assert_called_once()

    marchive_obj = MagicMock()
    filter_.last.return_value = marchive_obj
    task_create_sirivm_zipfile()
    marchive_obj.save.assert_called_once_with()


@patch("transit_odp.avl.tasks.CAVLDataArchive")
@patch("transit_odp.avl.tasks.requests")
def test_task_create_sirivm_zipfile_exception(mrequests, marchive):
    mrequests.get.side_effect = RequestException
    task_create_sirivm_zipfile()
    assert not marchive.objects.objects.last.called


def test_no_feeds_doesnt_break(mocker):
    data = []
    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()


def test_inconsistant_api_doesnt_break(mocker):
    """Tests dataset exists in database but not in cavl service"""
    DatasetFactory(dataset_type=AVLType)
    data = []
    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()


def test_no_change(mocker, mailoutbox):
    """tests cavl service reflects whats in the database"""
    subscribers = UserFactory.create_batch(3, account_type=DeveloperType)
    for user in subscribers:
        # created in post save signal so cant add in factory
        user.settings.notify_avl_unavailable = True
        user.settings.save()

    datasets = DatasetFactory.create_batch(
        3, dataset_type=AVLType, avl_feed_status=AVLFeedUp, subscribers=subscribers
    )
    data = []
    for dataset in datasets:
        dataset.contact.settings.notify_avl_unavailable = True
        dataset.contact.settings.save()
        data.append(
            AVLFeed(
                id=dataset.id,
                publisher_id=dataset.contact.id,
                url="www.testurl.com/avl",
                username=dataset.contact.username,
                password="password",
                status=dataset.avl_feed_status,
            )
        )

    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()
    assert len(mailoutbox) == 0
    assert (
        Dataset.objects.filter(
            dataset_type=AVLType, avl_feed_status=AVLFeedDown
        ).count()
        == 0
    )


def test_from_down_to_up_only_subscribers(mocker, mailoutbox):
    subscriber = UserFactory(account_type=DeveloperType)
    subscriber.settings.notify_avl_unavailable = True
    subscriber.settings.save()
    dataset = DatasetFactory(
        dataset_type=AVLType, avl_feed_status=AVLFeedDown, subscribers=[subscriber]
    )
    dataset.live_revision.status = FeedStatus.error.value
    dataset.live_revision.save()
    dataset.contact.settings.notify_avl_unavailable = True
    dataset.contact.settings.save()
    data = [
        AVLFeed(
            id=dataset.id,
            publisher_id=dataset.contact.id,
            url="www.testurl.com/avl",
            username=dataset.contact.username,
            password="password",
            status=AVLFeedStatus.FEED_UP,
        )
    ]

    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Data feed status changed"
    assert mailoutbox[0].to[0] == subscriber.email
    db_dataset = Dataset.objects.get(id=dataset.id)
    assert db_dataset.avl_feed_status == AVLFeedUp
    assert db_dataset.live_revision.status == FeedStatus.live.value


def test_from_up_to_down_email_everyone(mocker, mailoutbox):
    subscriber = UserFactory(account_type=DeveloperType)
    subscriber.settings.notify_avl_unavailable = True
    subscriber.settings.save()
    dataset = DatasetFactory(
        dataset_type=AVLType, avl_feed_status=AVLFeedUp, subscribers=[subscriber]
    )
    dataset.contact.settings.notify_avl_unavailable = True
    dataset.contact.settings.save()
    data = [
        AVLFeed(
            id=dataset.id,
            publisher_id=dataset.contact.id,
            url="www.testurl.com/avl",
            username=dataset.contact.username,
            password="password",
            status=AVLFeedStatus.FEED_DOWN,
        )
    ]

    service = Mock()
    service.get_feeds.return_value = data
    mocker.patch(CAVL_PATH, return_value=service)
    task_monitor_avl_feeds()
    assert len(mailoutbox) == 2
    developer, publisher = mailoutbox

    assert developer.subject == "Data feed status changed"
    assert developer.to[0] == subscriber.email

    assert (
        publisher.subject
        == f"AVL Feed {dataset.id} is no longer sending data to the Bus Open Data "
        f"Service"
    )
    assert publisher.to[0] == dataset.contact.email

    db_dataset = Dataset.objects.get(id=dataset.id)
    assert db_dataset.avl_feed_status == AVLFeedDown
    assert db_dataset.live_revision.status == FeedStatus.error.value


class TestValidateAVLTask:
    @pytest.mark.parametrize(
        "avl_status,expected_status,expected_version",
        [
            ("FEED_VALID", "SUCCESS", "2.0"),
            ("FEED_INVALID", "FAILURE", "0.0"),
            ("SYSTEM_ERROR", "FAILURE", "0.0"),
        ],
    )
    def test_task_validate_avl_feed(
        self, avl_status, expected_status, expected_version, mocker
    ):
        url = "https://cavlvalidation.com"
        username = "user"
        password = "pass"
        data = {
            "version": expected_version,
            "status": avl_status,
            "url": url,
            "username": username,
            "password": password,
            "created": datetime.now().isoformat(),
        }
        service = Mock()
        service.validate_feed.return_value = Mock(data=json.dumps(data))
        revision = DatasetRevisionFactory(
            username=username, password=password, url_link=url
        )
        DatasetMetadataFactory(revision=revision)
        mocker.patch(CAVL_PATH, return_value=service)
        task_id = uuid.uuid4()
        CAVLValidationTaskResultFactory(task_id=task_id, revision=revision)
        task_validate_avl_feed(task_id)
        service.validate_feed.assert_called_once_with(
            url=url,
            username=username,
            password=password,
            _request_timeout=60,
            _preload_content=False,
        )

        task = CAVLValidationTaskResult.objects.get(task_id=task_id)
        assert task.status == expected_status
        assert task.revision.metadata.schema_version == expected_version
