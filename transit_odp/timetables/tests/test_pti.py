from pathlib import Path

import pytest

from transit_odp.data_quality.models.report import PTIValidationResult
from transit_odp.data_quality.pti.factories import ViolationFactory
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.timetables.pti import DatasetPTIValidator
from transit_odp.timetables.tasks import task_pti_validation
from transit_odp.timetables.utils import get_pti_validator
from transit_odp.validate.exceptions import ValidationException

DATA_DIR = Path(__file__).parent / "data"

pytestmark = pytest.mark.django_db

TASKS = "transit_odp.timetables.tasks"
GET_TASK = TASKS + ".get_etl_task_or_pipeline_exception"
GET_VALIDATOR = TASKS + ".get_pti_validator"


def test_pti_validation():
    """
    Given a revision with a file containing pti violations
    When we call `get_violations` on the pti validator
    Then the number of violations returned is greater than 0
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())
    pti = get_pti_validator()
    violations = pti.get_violations(revision)
    assert len(violations) > 0


def test_validate_pti_success(mocker):
    """
    Given revision with a file containing pti violations
    When calling `task_pti_validation` function
    Then a PTIValidationResult object is created with a `count` of 1, `is_compliant`
    is False and the `DatasetPTIValidator.get_violations` is called once.
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())
    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    violation = ViolationFactory(filename=filepath.name)
    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.return_value = [violation]
    mocker.patch(GET_VALIDATOR, return_value=validator)

    task_pti_validation(revision.id, task.id)

    result = PTIValidationResult.objects.get(revision=revision)
    assert result.count == 1
    assert not result.is_compliant
    validator.get_violations.assert_called_once_with(revision=revision)


def test_validate_pti_multiple_calls(mocker):
    """
    Given a revision with a file with pti violations
    When the `task_pti_validation` function is called twice
    Then the old PTIValidationResult should be deleted and a new PTIValidationResult
    should be created with the same `count`.
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())

    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    violation = ViolationFactory(filename=filepath.name)
    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.return_value = [violation]
    mocker.patch(GET_VALIDATOR, return_value=validator)

    task_pti_validation(revision.id, task.id)
    original_result = PTIValidationResult.objects.get(revision=revision)

    task_pti_validation(revision.id, task.id)
    new_result = PTIValidationResult.objects.get(revision=revision)

    assert original_result.count == new_result.count
    assert original_result != new_result


def test_validate_pti_exception(mocker):
    """
    Given a revision with a file that contains pti violations
    When a call to `task_pti_validation` results in a PipelineException
    Then no PTIValidationResult object should be created and the DatasetETLResult
    task should be put to an error status.
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())

    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.side_effect = ValidationException(filename=filepath.name)
    mocker.patch(GET_VALIDATOR, return_value=validator)

    with pytest.raises(PipelineException):
        task_pti_validation(revision.id, task.id)

    results = PTIValidationResult.objects.filter(revision=revision)
    assert results.count() == 0
    assert not task.update_progress.called
    validator.get_violations.assert_called_once_with(revision=revision)
    task.to_error.assert_called_once()
    task.save.assert_called_once()
