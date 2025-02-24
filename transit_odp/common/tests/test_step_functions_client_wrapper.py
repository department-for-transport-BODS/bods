import re
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

from transit_odp.common.utils.aws_common import StepFunctionsClientWrapper


@pytest.fixture
def mock_boto_client(mocker):
    return mocker.patch("boto3.client")


@pytest.fixture
def stepfunctions_wrapper():
    return StepFunctionsClientWrapper()


@patch("transit_odp.common.utils.aws_common.settings")
def test_init_local(mock_settings, mock_boto_client):
    mock_settings.AWS_ENVIRONMENT = "LOCAL"
    mock_settings.AWS_REGION_NAME = "eu-west-1"
    mock_settings.AWS_ACCESS_KEY_ID = "test"
    mock_settings.AWS_SECRET_ACCESS_KEY = "test"

    wrapper = StepFunctionsClientWrapper()
    mock_boto_client.assert_called_once_with(
        "stepfunctions",
        region_name="eu-west-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


@patch("transit_odp.common.utils.aws_common.settings")
def test_init_default(mock_settings, mock_boto_client):
    mock_settings.AWS_ENVIRONMENT = "PROD"
    wrapper = StepFunctionsClientWrapper()
    mock_boto_client.assert_called_once_with("stepfunctions")


@patch("boto3.client", side_effect=NoCredentialsError)
def test_init_no_credentials(mock_boto_client):
    with pytest.raises(NoCredentialsError):
        StepFunctionsClientWrapper()


@patch(
    "boto3.client", side_effect=PartialCredentialsError(provider="aws", cred_var="key")
)
def test_init_partial_credentials(mock_boto_client):
    with pytest.raises(PartialCredentialsError):
        StepFunctionsClientWrapper()


@patch("boto3.client")
def test_start_step_function(mock_boto_client):
    # Mock boto3 Step Functions client
    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    mock_client.start_execution.return_value = {"executionArn": "test-execution-arn"}

    stepfunctions_wrapper = StepFunctionsClientWrapper()

    stepfunctions_wrapper.start_step_function("{}", "test-arn", "test-name")

    mock_client.start_execution.assert_called_once_with(
        stateMachineArn="test-arn",
        name="test-name",
        input="{}",
    )
    assert stepfunctions_wrapper.execution_arn == "test-execution-arn"


@pytest.mark.parametrize(
    "input_payload, expected_name",
    [
        (
            '{"s3": {"object": "coach-data/zip/2024-01-03-CoachData.zip"},"inputDataSource": "S3_FILE","datasetRevisionId": 123, "datasetType": "timetables","publishDatasetRevision":false}',
            r"123_\d{8}_\d{6}",
        ),
        (
            '{"url": "https://s3.eu-west-1.amazonaws.com/file_123.zip","inputDataSource": "URL_DOWNLOAD", "datasetType": "timetables","publishDatasetRevision":true}',
            r"unknown_\d{8}_\d{6}",
        ),
        ('{"datasetRevisionId": "rev@!#"}', r"rev_\d{8}_\d{6}"),
    ],
)
def test_clean_state_machine_name(input_payload, expected_name, stepfunctions_wrapper):
    name = stepfunctions_wrapper.clean_state_machine_name(input_payload)
    assert re.match(expected_name, name)
    assert len(name) <= 80


@pytest.mark.parametrize(
    "invalid_json",
    [
        "{invalid_json}",  # Malformed JSON
        "",  # Empty string
        "null",  # Valid JSON but not a dictionary
        "42",  # Valid JSON number but not a dictionary
        "[]",  # Valid JSON list but not a dictionary
    ],
)
def test_clean_state_machine_name_invalid_json(invalid_json, stepfunctions_wrapper):
    with pytest.raises(ValueError, match="Invalid JSON payload"):
        stepfunctions_wrapper.clean_state_machine_name(invalid_json)
