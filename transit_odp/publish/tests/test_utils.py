import json
from unittest.mock import Mock

import pytest

from transit_odp.pipelines.factories import (
    DatasetETLTaskResultFactory,
    DatasetRevisionFactory,
)
from transit_odp.publish.views.utils import create_state_machine_payload

pytestmark = pytest.mark.django_db


def test_create_payload_url_upload():
    mock_revision = DatasetRevisionFactory(
        id=123,
        url_link="https://example.com",
        upload_file=None,
    )

    task = DatasetETLTaskResultFactory(revision=mock_revision)

    payload_json = create_state_machine_payload(
        mock_revision, task.id, True, "timetables"
    )
    payload = json.loads(payload_json)
    assert payload is not None
    assert payload["datasetRevisionId"] == 123
    assert payload["datasetType"] == "timetables"
    assert payload["url"] == "https://example.com"
    assert payload["inputDataSource"] == "URL_DOWNLOAD"
    assert payload["publishDatasetRevision"]
    assert payload["datasetETLTaskResultId"] == task.id
    assert "s3" not in payload  # Ensure 's3' is excluded when None

    payload_json_fares = create_state_machine_payload(
        mock_revision, task.id, False, "fares"
    )
    payload = json.loads(payload_json_fares)
    assert payload is not None
    assert payload["datasetRevisionId"] == 123
    assert payload["datasetType"] == "fares"
    assert payload["url"] == "https://example.com"
    assert payload["inputDataSource"] == "URL_DOWNLOAD"
    assert not payload["publishDatasetRevision"]
    assert payload["datasetETLTaskResultId"] == task.id
    assert "s3" not in payload  # Ensure 's3' is excluded when None


def test_create_payload_file_upload():
    mock_file = Mock()
    mock_file.name = "test_file"

    mock_revision = DatasetRevisionFactory(
        id=123,
        url_link="",
    )

    task = DatasetETLTaskResultFactory(revision=mock_revision)

    payload_json = create_state_machine_payload(
        mock_revision, task.id, False, "timetables"
    )
    payload = json.loads(payload_json)
    assert payload is not None
    assert payload["datasetRevisionId"] == 123
    assert payload["datasetType"] == "timetables"
    assert payload["inputDataSource"] == "S3_FILE"
    assert payload["s3"]["object"] == "transXchange.xml"
    assert not payload["publishDatasetRevision"]
    assert payload["datasetETLTaskResultId"] == task.id
    assert "url" not in payload  # Ensure 'url' is excluded when None

    payload_json_fares = create_state_machine_payload(
        mock_revision, task.id, True, "fares"
    )
    payload = json.loads(payload_json_fares)
    assert payload is not None
    assert payload["datasetRevisionId"] == 123
    assert payload["datasetType"] == "fares"
    assert payload["inputDataSource"] == "S3_FILE"
    assert payload["s3"]["object"] == "transXchange.xml"
    assert payload["publishDatasetRevision"]
    assert payload["datasetETLTaskResultId"] == task.id
    assert "url" not in payload  # Ensure 'url' is excluded when None


def test_create_payload_missing_inputs(caplog):
    mock_revision = DatasetRevisionFactory(
        id=123,
        url_link="",
        upload_file=None,
    )

    task = DatasetETLTaskResultFactory(revision=mock_revision)

    payload_json = create_state_machine_payload(mock_revision, task.id)
    assert payload_json == {}
    assert (
        "Both URL link and uploaded file are missing in the dataset revision."
        in caplog.text
    )
