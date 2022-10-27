from datetime import timedelta
from pathlib import Path

import pytest
from django.utils import timezone

from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.proxies import TimetableDatasetRevision
from transit_odp.timetables.tasks import task_scan_timetables
from transit_odp.timetables.validate import TXCRevisionValidator
from transit_odp.validate.antivirus import (
    AntiVirusError,
    ClamConnectionError,
    SuspiciousFile,
)
from transit_odp.validate.xml import DangerousXML, XMLSyntaxError, XMLValidator

pytestmark = pytest.mark.django_db

TASKS = "transit_odp.timetables.tasks"
GET_TASK = TASKS + ".get_etl_task_or_pipeline_exception"
FILE_SCANNER = TASKS + ".FileScanner"

DATA_DIR = Path(__file__).parent.joinpath("data")
XML_FILE = DATA_DIR.joinpath("ea_20-1A-A-y08-1.xml")
ZIP_FILE = DATA_DIR.joinpath("EA_TXC_5_files.zip")


class TestFileValidation:
    def test_malformed_xml(self):
        """Tests a malformed xml file fails the pipeline"""
        path = str(DATA_DIR.joinpath("bad.xml"))
        with open(path, "rb") as fin:
            with pytest.raises(XMLSyntaxError) as exc_info:
                XMLValidator(fin).validate()
            assert exc_info.value.filename == path

    @pytest.mark.parametrize(
        "filename",
        [
            "xml_bomb.xml",
            "quadratic_blow_up.xml",
            "txc_with_dtd.xml",
            "txc_with_local_entity.xml",
            "txc_with_remote_entity.xml",
        ],
    )
    def test_malicious_file(self, filename):
        """Tests DangerousXMLError is raised for malicious XML files.

        See https://pypi.org/project/defusedxml/#attack-vectors
        """
        path = str(DATA_DIR.joinpath(filename))
        with open(path, "rb") as fin:
            with pytest.raises(DangerousXML) as exc_info:
                XMLValidator(fin).validate()
            assert exc_info.value.filename == path


class TestPipeline:
    @pytest.mark.parametrize(
        "side_effect,expectaton,task_status",
        [
            (
                SuspiciousFile(
                    filename="test.xml",
                    message="Anti-virus alert triggered for file text.xml.",
                ),
                pytest.raises(PipelineException),
                DatasetETLTaskResult.SUSPICIOUS_FILE,
            ),
            (
                AntiVirusError(
                    filename="test.xml",
                    message="Antivirus failed validating file text.xml.",
                ),
                pytest.raises(PipelineException),
                AntiVirusError.code,
            ),
            (
                ClamConnectionError(
                    filename="test.xml",
                    message="Could not connect to Clam daemon when testing test.xml.",
                ),
                pytest.raises(PipelineException),
                ClamConnectionError.code,
            ),
        ],
    )
    def test_antivirus_scan_sets_task_error_code(
        self, side_effect, expectaton, task_status, mocker
    ):
        """
        Tests antivirus_scan sets task error_code if it fails
        """
        revision = DatasetRevisionFactory(upload_file__filename="test.xml")

        scanner = mocker.Mock()
        scanner.scan.side_effect = side_effect
        mocker.patch(FILE_SCANNER, return_value=scanner)

        task = mocker.Mock(revision=revision, id=-1)
        mocker.patch(GET_TASK, return_value=task)

        with expectaton:
            task_scan_timetables(revision.id, task.id)

        task.to_error.assert_called_once_with("dataset_validate", task_status)


def test_revision_get_by_service_code_non_unique():
    """
    GIVEN a DatasetRevision with two TXCFileAttributes with the same service_code.
    WHEN `get_live_attribute_by_service_code` is called.
    THEN a list of TXCFileAttributes are returned ordered in ascending order by
    revision_number
    """
    revision = DatasetRevisionFactory(upload_file=None)
    service_code = "ABC"
    t1 = TXCFileAttributesFactory(
        revision=revision, service_code=service_code, revision_number=0
    )
    t2 = TXCFileAttributesFactory(
        revision=revision, service_code=service_code, revision_number=2
    )

    validator = TXCRevisionValidator(revision)
    expected = [t1, t2]
    actual = validator.get_live_attribute_by_service_code(service_code)
    assert expected == actual


def test_revision_get_by_service_code_and_lines():
    """
    GIVEN a DatasetRevision with two TXCFileAttributes with the same service_code and
    lines.
    WHEN `get_live_attribute_by_service_code` is called.
    THEN a list of TXCFileAttributes are returned ordered in ascending order by
    revision_number
    """
    revision = DatasetRevisionFactory(upload_file=None)
    service_code = "ABC"
    lines = ["1", "2"]
    t1 = TXCFileAttributesFactory(
        revision=revision,
        service_code=service_code,
        revision_number=0,
        line_names=lines,
    )
    t2 = TXCFileAttributesFactory(
        revision=revision,
        service_code=service_code,
        revision_number=2,
        line_names=lines,
    )

    TXCFileAttributesFactory(
        revision=revision,
        service_code=service_code,
        revision_number=2,
    )

    validator = TXCRevisionValidator(revision)
    expected = [t1, t2]
    actual = validator.get_live_attribute_by_service_code_and_lines(service_code, lines)
    assert expected == actual


def test_filter_by_service_code_and_lines_matches_lines_in_any_order():
    """
    GIVEN a DatasetRevision with two TXCFileAttributes with the same service_code and
    lines that are not in order.
    WHEN `get_live_attribute_by_service_code` is called.
    THEN a list of TXCFileAttributes are returned ordered in ascending order by
    revision_number
    """
    revision = DatasetRevisionFactory(upload_file=None)
    service_code = "ABC"
    t1 = TXCFileAttributesFactory(
        revision=revision,
        service_code=service_code,
        revision_number=0,
        line_names=["1", "2"],
    )
    t2 = TXCFileAttributesFactory(
        revision=revision,
        service_code=service_code,
        revision_number=2,
        line_names=["2", "1"],
    )

    validator = TXCRevisionValidator(revision)
    expected = [t1, t2]
    actual = validator.get_live_attribute_by_service_code_and_lines(
        service_code, t1.line_names
    )
    assert expected == actual
    actual = validator.get_live_attribute_by_service_code_and_lines(
        service_code, t2.line_names
    )
    assert expected == actual


@pytest.mark.parametrize(
    ("live_number", "draft_number", "modification_datetime_changed", "violation_count"),
    [
        (0, 1, True, 0),
        (2, 2, True, 1),
        (2, 3, True, 0),
        (2, 3, False, 1),
        (2, 1, False, 1),
        (2, 1, True, 1),
    ],
)
def test_revision_number_violation(
    live_number, draft_number, modification_datetime_changed, violation_count
):
    """
    Given a Dataset with live revision and a draft revision

    When the modification_datetime has changed and revision_number has not
    Then a violation is generated

    When the modification_datetime has changed and revision_number has
    been decremented
    Then a violation is generated

    When the modification_datetime is unchanged between revisions
    Then no violation is generated regardless of the revision_number
    """
    dataset = DatasetFactory()
    live_revision = DatasetRevisionFactory(
        dataset=dataset, upload_file=None, is_published=True
    )
    draft_revision = DatasetRevisionFactory(
        dataset=dataset, upload_file=None, is_published=False
    )
    dataset.live_revision = live_revision
    dataset.save()

    now = timezone.now()
    if modification_datetime_changed:
        live_modification_datetime = now - timedelta(days=1)
        draft_modification_datetime = now
    else:
        live_modification_datetime = now
        draft_modification_datetime = now

    service_code = "ABC"
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=service_code,
        revision_number=live_number,
        modification_datetime=live_modification_datetime,
    )
    TXCFileAttributesFactory(
        revision=draft_revision,
        service_code=service_code,
        revision_number=draft_number,
        modification_datetime=draft_modification_datetime,
    )

    validator = TXCRevisionValidator(
        TimetableDatasetRevision.objects.get(id=draft_revision.id)
    )
    validator._live_hashes = list(
        live_revision.txc_file_attributes.values_list("hash", flat=True)
    )
    validator.validate_revision_number()
    assert len(validator.violations) == violation_count


@pytest.mark.parametrize(
    (
        "live_number",
        "draft_number",
        "live_lines",
        "draft_lines",
        "violation_count",
    ),
    [
        (0, 1, ["line1", "line2"], ["line1", "line2"], 0),
        (2, 2, ["line1", "line2"], ["line1", "line2"], 1),
        (2, 3, ["line1", "line2"], ["line2", "line1"], 0),
        (2, 1, ["line1", "line2"], ["line1", "line2"], 1),
        (2, 1, ["line1", "line2"], ["line2", "line1"], 1),
        (1, 2, ["34"], ["34"], 0),
        (1, 1, ["33"], ["34"], 0),
    ],
)
def test_revision_number_service_and_line_violation(
    live_number, draft_number, live_lines, draft_lines, violation_count
):
    """
    Given a Dataset with live revision and a draft revision

    When the lines match and revision_number has been decremented
    Then a violation is generated

    When the lines dont match and revision_number has been decremented
    Then a violation is not generated

    When the lines match and revision_number has been incremented
    Then a violation is not generated

    """
    dataset = DatasetFactory()
    live_revision = DatasetRevisionFactory(
        dataset=dataset, upload_file=None, is_published=True
    )
    draft_revision = DatasetRevisionFactory(
        dataset=dataset, upload_file=None, is_published=False
    )
    dataset.live_revision = live_revision
    dataset.save()

    now = timezone.now()
    live_modification_datetime = now - timedelta(days=1)
    draft_modification_datetime = now

    service_code = "ABC"
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=service_code,
        revision_number=live_number,
        line_names=live_lines,
        modification_datetime=live_modification_datetime,
    )
    TXCFileAttributesFactory(
        revision=draft_revision,
        service_code=service_code,
        revision_number=draft_number,
        modification_datetime=draft_modification_datetime,
        line_names=draft_lines,
    )

    validator = TXCRevisionValidator(
        TimetableDatasetRevision.objects.get(id=draft_revision.id)
    )
    validator._live_hashes = list(
        live_revision.txc_file_attributes.values_list("hash", flat=True)
    )
    validator.validate_revision_number()
    assert len(validator.violations) == violation_count
