from pathlib import Path

import pytest

from transit_odp.data_quality.models.report import PTIObservation
from transit_odp.data_quality.pti.factories import ViolationFactory
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.timetables.pti import DatasetPTIValidator
from transit_odp.timetables.tasks import run_pti_validation
from transit_odp.timetables.utils import get_pti_validator
from transit_odp.validate.exceptions import ValidationException

DATA_DIR = Path(__file__).parent / "data"

pytestmark = pytest.mark.django_db

TASKS = "transit_odp.timetables.tasks"
GET_TASK = TASKS + ".get_etl_task_or_pipeline_exception"
GET_VALIDATOR = TASKS + ".get_pti_validator"


@pytest.mark.parametrize("filepath,expected", [(DATA_DIR / "pti_xml_test.xml", 0)])
def test_pti_validation(filepath, expected):
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())
    pti = get_pti_validator()
    violations = pti.get_violations(revision)
    assert len(violations) > 0


@pytest.mark.parametrize(
    "filepath, expectation",
    [(DATA_DIR / "pti_xml_test.xml", 0)],
)
def test_validate_pti_success(filepath, expectation, mocker):
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())

    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    violation = ViolationFactory(filename=filepath.name)
    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.return_value = [violation]
    mocker.patch(GET_VALIDATOR, return_value=validator)

    run_pti_validation(task.id)

    observations = PTIObservation.objects.filter(revision=revision)
    assert observations.count() == 1
    assert observations.first().details == violation.observation.details
    validator.get_violations.assert_called_once_with(revision=revision)


def test_validate_pti_multiple_calls(mocker):
    """
    Multiple calls to the validation pipeline should not double up the observation
    count.
    """
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())

    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    violation = ViolationFactory(filename=filepath.name)
    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.return_value = [violation]
    mocker.patch(GET_VALIDATOR, return_value=validator)

    run_pti_validation(task.id)
    original_count = PTIObservation.objects.filter(revision=revision).count()
    original_observation = PTIObservation.objects.filter(revision=revision).first()

    run_pti_validation(task.id)
    new_count = PTIObservation.objects.filter(revision=revision).count()
    new_observation = PTIObservation.objects.filter(revision=revision).first()

    assert original_count == new_count
    assert original_observation != new_observation


def test_validate_pti_exception(mocker):
    filepath = DATA_DIR / "pti_xml_test.xml"
    revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())

    task = mocker.Mock(revision=revision, id=-1)
    mocker.patch(GET_TASK, return_value=task)

    validator = mocker.Mock(spec=DatasetPTIValidator)
    validator.get_violations.side_effect = ValidationException(filename=filepath.name)
    mocker.patch(GET_VALIDATOR, return_value=validator)

    with pytest.raises(PipelineException):
        run_pti_validation(task.id)

    observations = PTIObservation.objects.filter(revision=revision)
    assert observations.count() == 0
    assert not task.update_progress.called
    validator.get_violations.assert_called_once_with(revision=revision)
    task.to_error.assert_called_once()
    task.save.assert_called_once()
