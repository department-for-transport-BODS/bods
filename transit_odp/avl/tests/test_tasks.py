import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from requests import RequestException

from transit_odp.avl.factories import CAVLValidationTaskResultFactory
from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.avl.tasks import task_create_sirivm_zipfile, task_validate_avl_feed
from transit_odp.organisation.factories import (
    DatasetMetadataFactory,
    DatasetRevisionFactory,
)

pytestmark = pytest.mark.django_db


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
        cavl_path = "transit_odp.avl.tasks.get_cavl_service"
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
        mocker.patch(cavl_path, return_value=service)
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
