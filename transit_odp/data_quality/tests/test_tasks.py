from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.files.base import ContentFile

from transit_odp.data_quality.tasks import download_dqs_report, upload_dataset_to_dqs
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.factories import (
    DataQualityTaskFactory,
    DatasetETLTaskResultFactory,
)
from transit_odp.pipelines.models import DataQualityTask, DatasetETLTaskResult

pytestmark = pytest.mark.django_db

TXC_PIPELINE = "transit_odp.timetables.tasks.TransXChangePipeline"


@patch("transit_odp.data_quality.tasks.upload_file_to_dqs")
def test_task_upload_file_success(upload):
    uuid = str(uuid4())
    upload.return_value = uuid

    revision = DatasetRevisionFactory()
    task = DatasetETLTaskResultFactory(revision=revision)
    dq_task = upload_dataset_to_dqs(task.id)

    upload.assert_called_once_with(revision.upload_file)
    assert dq_task.task_id == uuid
    assert dq_task.status == DataQualityTask.RECEIVED


@patch("transit_odp.data_quality.tasks.upload_file_to_dqs")
def test_task_upload_file_no_uuid(upload):
    upload.return_value = None
    revision = DatasetRevisionFactory()
    task = DatasetETLTaskResultFactory(revision=revision)
    with pytest.raises(PipelineException) as exc:
        upload_dataset_to_dqs(task.id)

    str(exc.value) == "DQS did not acknowledge task"
    upload.assert_called_once_with(revision.upload_file)


@patch("transit_odp.data_quality.tasks.upload_file_to_dqs", side_effect=Exception)
def test_task_upload_file_dqs_exception(upload):
    revision = DatasetRevisionFactory(status=FeedStatus.indexing.value)
    task = DatasetETLTaskResultFactory(revision=revision)
    with pytest.raises(PipelineException) as exc:
        upload_dataset_to_dqs(task.id)

    task.refresh_from_db()
    str(exc.value) == "Unknown error with DQS."
    upload.assert_called_once_with(revision.upload_file)
    assert task.error_code == DatasetETLTaskResult.SYSTEM_ERROR
    assert DataQualityTask.objects.last().status == DataQualityTask.FAILURE


"""
    _prefix = f"[DQS] DataQualityTask {pk} => "
    logger.info(_prefix + "Downloading DQS report json file.")

    task = get_data_quality_task_or_pipeline_error(pk)

    file_ = create_dqs_report(task.task_id)
    filename = f"dqs_report_{task.task_id}.json"
    report = DataQualityReport(revision=task.revision)
    report.file.save(filename, file_)
    logger.info(_prefix + "DataQualityReport successfully created.")

    task.report = report
    task.save()
    logger.info(_prefix + "Report added to task.")
    return report
"""


@patch("transit_odp.data_quality.tasks.create_dqs_report")
def test_download_dqs_file(create_report):
    create_report.return_value = ContentFile(b'{"one": "two"}')
    task = DataQualityTaskFactory()
    download_dqs_report(task.id)
    task.refresh_from_db()

    create_report.assert_called_once_with(task.task_id)
    assert task.report is not None
    assert task.report.file.name == f"dqs_report_{task.task_id}.json"
