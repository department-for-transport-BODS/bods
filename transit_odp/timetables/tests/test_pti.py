from pathlib import Path

import pytest

from transit_odp.data_quality.models.report import PTIObservation, PTIValidationResult
from transit_odp.data_quality.pti.factories import ViolationFactory
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.timetables.proxies import TimetableDatasetRevision
from transit_odp.timetables.pti import DatasetPTIValidator, get_pti_validator
from transit_odp.timetables.tasks import task_pti_validation

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
    revision = DatasetRevisionFactory(
        upload_file__from_path=filepath.as_posix(), is_published=False
    )
    pti = get_pti_validator()
    violations = pti.get_violations(
        TimetableDatasetRevision.objects.get(id=revision.id)
    )
    assert len(violations) > 0


def test_pti_validation_passes_on_zip():
    """
    Given a revision with a zipfile containing no pti violations
    When we call `get_violations` on the pti validator
    Then the number of violations returned is 0
    """
    filepath = DATA_DIR / "3_pti_pass.zip"
    revision = DatasetRevisionFactory(
        upload_file__from_path=filepath.as_posix(), is_published=False
    )
    pti = get_pti_validator()
    violations = pti.get_violations(
        TimetableDatasetRevision.objects.get(id=revision.id)
    )
    assert len(violations) == 0


def test_pti_validation_passes_on_zip_with_same_draft():
    """
    Given a revision with a zipfile containing no pti violations
    When we call `get_violations` on the pti validator
    Then the number of violations returned is 0
    """
    filepath = DATA_DIR / "3_pti_pass.zip"
    draft = DatasetRevisionFactory(
        upload_file__from_path=filepath.as_posix(), is_published=False
    )
    DatasetRevisionFactory(
        upload_file__from_path=filepath.as_posix(),
        is_published=True,
        dataset=draft.dataset,
    )
    pti = get_pti_validator()
    violations = pti.get_violations(TimetableDatasetRevision.objects.get(id=draft.id))
    assert len(violations) == 0


def test_validate_pti_success(mocker, pti_unenforced):
    """
    Given revision with a file containing pti violations
    When calling `task_pti_validation` function
    Then a PTIValidationResult object is created with a `count` of 1, `is_compliant`
    is False and the `DatasetPTIValidator.get_violations` is called once.
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())
    TXCFileAttributesFactory(revision=revision)
    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    violation = ViolationFactory(filename=filepath.name)
    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.return_value = [violation]
    mocker.patch(GET_VALIDATOR, return_value=validator)

    with pytest.raises(PipelineException):
        task_pti_validation(revision.id, task.id)

    result = PTIValidationResult.objects.get(revision=revision)
    pti_observation_result = PTIObservation.objects.filter(revision_id=revision.id)
    assert pti_observation_result.count() == 1
    assert result.count == 1
    assert not result.is_compliant
    validator.get_violations.assert_called_once_with(revision=revision)


def test_validate_pti_multiple_calls(mocker, pti_unenforced):
    """
    Given a revision with a file with pti violations
    When the `task_pti_validation` function is called twice
    Then the old PTIValidationResult should be deleted and a new PTIValidationResult
    should be created with the same `count`.
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())
    TXCFileAttributesFactory(revision=revision)

    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    violation = ViolationFactory(filename=filepath.name)
    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.return_value = [violation]
    mocker.patch(GET_VALIDATOR, return_value=validator)

    with pytest.raises(PipelineException):
        task_pti_validation(revision.id, task.id)
    original_result = PTIValidationResult.objects.get(revision=revision)

    with pytest.raises(PipelineException):
        task_pti_validation(revision.id, task.id)
    new_result = PTIValidationResult.objects.get(revision=revision)

    pti_observation_result = PTIObservation.objects.filter(revision_id=revision.id)
    assert pti_observation_result.count() == 1
    assert original_result.count == new_result.count
    assert original_result != new_result


def test_validate_pti_exception_with_no_valid_txc_files(mocker, pti_unenforced):
    """
    Given a revision with a file that contains pti violations and no entry in
    txcfileattributes table. When a call to `task_pti_validation` results
    in a PipelineException
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())

    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    with pytest.raises(PipelineException):
        task_pti_validation(revision.id, task.id)
