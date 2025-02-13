import csv
import io
from unittest.mock import MagicMock

import pytest

from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.timetables.views.constants import (
    ADDITIONAL_SERVICES_PII,
    ERROR_TYPE_PII,
    ERROR_TYPE_SERVICE_CHECK,
    LINK_PII,
    NEXT_STEPS_PII,
    NEXT_STEPS_SERVICE_CHECK,
)
from transit_odp.timetables.views.post_schema import PostSchemaCSV, PostSchemaErrorType

pytestmark = pytest.mark.django_db


def test_get_queryset(mocker):
    revision = DatasetRevisionFactory()
    mock_qs = mocker.patch(
        "transit_odp.data_quality.models.report.PostSchemaViolation.objects.filter"
    )
    instance = PostSchemaCSV(revision)
    assert instance.queryset == mock_qs.return_value
    mock_qs.assert_called_once_with(revision_id=revision.id)


def test_annotate_pii_qs():
    revision = DatasetRevisionFactory()
    instance = PostSchemaCSV(revision)
    row_data = {}
    result = instance.annotate_pii_qs(row_data)
    assert result["Error Type"] == ERROR_TYPE_PII
    assert result["Next Steps"] == NEXT_STEPS_PII
    assert result["Link to Next Steps Column"] == LINK_PII
    assert result["Additional Information"] == ADDITIONAL_SERVICES_PII


def test_annotate_check_service_qs():
    revision = DatasetRevisionFactory()
    instance = PostSchemaCSV(revision)
    row_data = {
        "Additional Information": {
            "published_dataset": 456,
            "service_codes": ["SC001", "SC002"],
        }
    }
    instance.get_dataset_link = MagicMock(return_value="mocked_link")
    result = instance.annotate_check_service_qs(row_data)
    assert result["Error Type"] == ERROR_TYPE_SERVICE_CHECK
    assert result["Next Steps"] == NEXT_STEPS_SERVICE_CHECK
    assert result["Link to Next Steps Column"] == "mocked_link"
    assert result["Additional Information"] == "SC001, SC002"


def test_to_string(mocker):
    revision = DatasetRevisionFactory()
    instance = PostSchemaCSV(revision)
    mock_queryset = [
        MagicMock(
            filename="file1",
            error_type=ERROR_TYPE_PII,
            next_steps=NEXT_STEPS_PII,
            link="link1",
            additional_details="details1",
            details=PostSchemaErrorType.PII_ERROR.value,
        ),
        MagicMock(
            filename="file2",
            error_type=ERROR_TYPE_SERVICE_CHECK,
            next_steps=NEXT_STEPS_SERVICE_CHECK,
            link="link2",
            additional_details="details2",
            details=PostSchemaErrorType.SERVICE_EXISTS.value,
        ),
    ]

    instance.queryset = mock_queryset
    instance.annotate_pii_qs = MagicMock(
        side_effect=lambda x: {**x, "Error Type": ERROR_TYPE_PII}
    )
    instance.annotate_check_service_qs = MagicMock(
        side_effect=lambda x: {**x, "Error Type": ERROR_TYPE_SERVICE_CHECK}
    )

    result = instance.to_string()

    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["Filename"] == "file1"
    assert rows[1]["Filename"] == "file2"
    assert rows[0]["Error Type"] == ERROR_TYPE_PII
    assert rows[1]["Error Type"] == ERROR_TYPE_SERVICE_CHECK
