from pathlib import Path
from unittest.mock import Mock

import pytest
from django.core.files import File
from django.utils import timezone
from freezegun import freeze_time
from requests import Response

from transit_odp.data_quality.models import SchemaViolation
from transit_odp.data_quality.models.report import (
    PostSchemaViolation,
    PTIValidationResult,
)
from transit_odp.fares.tasks import DT_FORMAT
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.constants import PII_ERROR
from transit_odp.timetables.tasks import (
    task_dataset_download,
    task_dataset_etl,
    task_post_schema_check,
    task_pti_validation,
    task_scan_timetables,
    task_timetable_file_check,
    task_timetable_schema_check,
)
from transit_odp.timetables.transxchange import BaseSchemaViolation
from transit_odp.users.factories import OrgAdminFactory
from transit_odp.validate import DownloadException, FileScanner
from transit_odp.validate.antivirus import AntiVirusError, SuspiciousFile
from transit_odp.validate.tests.utils import (
    create_sparse_file,
    create_text_file,
    create_zip_file,
)

pytestmark = pytest.mark.django_db

TASK_MODULE = "transit_odp.timetables.tasks"
HERE = Path(__file__)
DATA = HERE.parent / "data"


class TransXChangeDatasetParserFactory:
    def __init__(self, source, failed_validations_filename):
        self.source = source
        self.failed_validations_filename = failed_validations_filename

    def get_documents(self):
        return []


class DatasetTXCValidatorFactory_No_Violation:
    def __init__(self, revision):
        self.revision = revision

    def get_violations(self):
        return []

    def get_number_of_files_uploaded(self):
        return 1


class DatasetTXCValidatorFactory:
    def __init__(self, revision):
        self.revision = revision

    def get_violations(self):
        return [
            BaseSchemaViolation(
                filename="failed_violation.xml", line=12, details="Invalid schema"
            )
        ]

    def get_number_of_files_uploaded(self):
        return 1


class PostSchemaValidatorFactory:
    def __init__(self):
        pass

    def get_violations(self):
        return [PII_ERROR]

    def get_failed_validation_filenames(self):
        return ["failed_postchema_violation.xml"]


class PostSchemaValidatorFactory_No_Violation:
    def __init__(self):
        pass

    def get_violations(self):
        return []

    def get_failed_validation_filenames(self):
        return []


@pytest.fixture
def mock_dataset_txc_validator():
    return DatasetTXCValidatorFactory(None)


@pytest.fixture
def mock_dataset_txc_validator_no_violation():
    return DatasetTXCValidatorFactory_No_Violation(None)


@pytest.fixture
def mock_post_schema_validator():
    return PostSchemaValidatorFactory()


@pytest.fixture
def mock_post_schema_validator_no_violation():
    return PostSchemaValidatorFactory_No_Violation()


@pytest.fixture
def mock_trans_xchange_dataset_parser():
    return TransXChangeDatasetParserFactory(None, None)


@pytest.fixture
def org_with_key_contact():
    return create_org_with_key_contact()


def create_org_with_key_contact():
    org = OrganisationFactory()
    org.key_contact = OrgAdminFactory(organisations=(org,))
    org.save()
    return org


def create_task(**kwargs):
    """A helper function to return a DatasetETLTaskResult."""
    return DatasetETLTaskResultFactory(
        revision__status=FeedStatus.indexing.value,
        revision__is_published=False,
        revision__published_at=timezone.now(),
        status=DatasetETLTaskResult.STARTED,
        **kwargs,
    )


def _add_revision(dataset, **kwargs):
    txc_version = kwargs.pop("txc_version", 2.1)
    status = kwargs.pop("status", FeedStatus.live.value)
    is_published = kwargs.pop("is_published", True)

    revision = DatasetRevisionFactory(
        transxchange_version=txc_version,
        dataset=dataset,
        status=status,
        is_published=is_published,
        **kwargs,
    )
    DatasetETLTaskResultFactory(revision=revision)
    return revision


def add_live_revision(dataset, txc_version=2.1):
    return _add_revision(dataset, txc_version=txc_version)


def add_draft_revision(dataset, txc_version=2.1, **kwargs):
    status = kwargs.pop("status", FeedStatus.success.value)
    return _add_revision(
        dataset,
        txc_version=txc_version,
        is_published=False,
        status=status,
        **kwargs,
    )


def create_datasets(organisation, txc_version=2.1):
    """
    helper function that returns the following datasets in a list:
    published dataset with 1 live revision
    published dataset with 1 live and one draft revision
    published dataset with 2 live revisions
    published dataset with 2 live and one draft revision
    draft dataset with 1 draft revision
    Note: each revision has an associated ETL task result
    """

    d1, d2, d3, d4 = DatasetFactory.create_batch(
        4,
        live_revision__transxchange_version=txc_version,
        organisation=organisation,
    )

    for dataset in d1, d2, d3, d4:
        DatasetETLTaskResultFactory(revision=dataset.live_revision)

    add_draft_revision(d2, txc_version=txc_version)
    add_live_revision(d3, txc_version=txc_version)
    add_live_revision(d4, txc_version=txc_version)
    add_draft_revision(d4, txc_version=txc_version)

    d5 = DatasetFactory(live_revision=None, organisation=organisation)
    add_draft_revision(d5, txc_version=txc_version)
    return d1, d2, d3, d4, d5


def test_task_run_download_with_no_task():
    """Given a task_id that doesn't exist, throw a PipelineException."""
    task_id = -1
    revision_id = -1
    with pytest.raises(PipelineException) as exc_info:
        task_dataset_download(revision_id, task_id)

    expected = f"DatasetETLTaskResult {task_id} does not exist."
    assert str(exc_info.value) == expected


def test_download_timetable_success(mocker):
    url_link = "http://fakeurl.com"
    task = create_task(revision__upload_file=None, revision__url_link=url_link)

    download_get = TASK_MODULE + ".DataDownloader.get"
    response = Mock(spec=Response, content=b"123", filetype="xml")
    mocker.patch(download_get, return_value=response)

    now = timezone.now()
    now_str = now.strftime(DT_FORMAT)
    with freeze_time(now):
        task_dataset_download(task.revision.id, task.id)
    task.refresh_from_db()

    revision = task.revision
    expected_filename = f"remote_dataset_{revision.dataset.id}_{now_str}.xml"
    assert revision.upload_file.read() == b"123"
    assert revision.upload_file.name == expected_filename


def test_download_timetable_exception(mocker):
    download_get = TASK_MODULE + ".DataDownloader.get"
    url_link = "http://fakeurl.com"
    task = create_task(revision__upload_file=None, revision__url_link=url_link)
    mocker.patch(download_get, side_effect=DownloadException(url_link))
    with pytest.raises(PipelineException) as exc_info:
        task_dataset_download(task.revision.id, task.id)

    task.refresh_from_db()
    assert task.error_code == task.SYSTEM_ERROR
    assert str(exc_info.value) == f"Unable to download data from {url_link}."


def test_download_timetable_no_file_or_url():
    """Given task has no file or url_link."""
    task = create_task(revision__upload_file=None)
    with pytest.raises(PipelineException) as exc_info:
        task_dataset_download(task.revision.id, task.id)

    expected = f"DatasetRevision {task.revision.id} doesn't contain a file."
    task.refresh_from_db()
    assert str(exc_info.value) == expected
    assert task.error_code == task.SYSTEM_ERROR


def test_run_timetable_txc_schema_validation_violation_found(
    mocker, tmp_path, mock_dataset_txc_validator
):
    """
    Given a zip file with an invalid xml a violation entry
    would be inserted in schemaviolation table.
    """

    file1 = tmp_path / "file1.xml"
    testzip = tmp_path / "testzip.zip"
    create_text_file(file1, "not xml")
    create_zip_file(testzip, [file1])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="testzip.zip"))

    zip_validator = TASK_MODULE + ".DatasetTXCValidator"
    mocker.patch(zip_validator, return_value=mock_dataset_txc_validator)

    task_timetable_schema_check(task.revision.id, task.id)
    schemaviolation_objects = SchemaViolation.objects.filter(
        revision_id=task.revision.id
    )
    assert schemaviolation_objects.count() == 1
    assert schemaviolation_objects.first().filename == "failed_violation.xml"


def test_task_timetable_schema_check_zip_no_violation(
    mocker, tmp_path, mock_dataset_txc_validator_no_violation
):
    """
    Given a zip file with valid xml no violation entry
    would be inserted in schemaviolation table.
    """
    xml_file = DATA / "test_flexible_and_standard_service.xml"
    testzip = tmp_path / "testzip.zip"
    create_zip_file(testzip, [xml_file])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="testzip.zip"))

    zip_validator = TASK_MODULE + ".DatasetTXCValidator"
    mocker.patch(zip_validator, return_value=mock_dataset_txc_validator_no_violation)

    task_timetable_schema_check(task.revision.id, task.id)
    schemaviolation_objects = SchemaViolation.objects.filter(
        revision_id=task.revision.id
    )
    assert schemaviolation_objects.count() == 0


def test_run_timetable_txc_schema_validation_exception(
    mocker, tmp_path, mock_dataset_txc_validator
):
    """
    Given a zip file with an invalid xml a violation entry will be inserted
    in SchemaViolation table and no Pipeline Exception would be raised
    """

    file1 = tmp_path / "file1.xml"
    testzip = tmp_path / "testzip.zip"
    create_text_file(file1, "not xml")
    create_zip_file(testzip, [file1])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="testzip.zip"))

    zip_validator = TASK_MODULE + ".DatasetTXCValidator"
    mocker.patch(zip_validator, return_value=mock_dataset_txc_validator)

    task_timetable_schema_check(task.revision.id, task.id)

    task.refresh_from_db()
    schemaviolation_objects = SchemaViolation.objects.filter(
        revision_id=task.revision.id
    )
    assert schemaviolation_objects.count() == 1


def test_run_timetable_txc_schema_validation_dangerous_xml_found(
    mocker, tmp_path, mock_dataset_txc_validator
):
    file1 = tmp_path / "file1.xml"
    create_sparse_file(file1, file_size=int(1e2))

    error_message = "Invalid schema"

    xml_validator = TASK_MODULE + ".DatasetTXCValidator"
    mocker.patch(xml_validator, return_value=mock_dataset_txc_validator)

    with open(file1, "rb") as f:
        task = create_task(revision__upload_file=File(f, name="file1.xml"))

    with pytest.raises(PipelineException):
        task_timetable_schema_check(task.revision.id, task.id)
    schemaviolation_objects = SchemaViolation.objects.filter(
        revision_id=task.revision.id
    )
    assert schemaviolation_objects.count() == 1
    assert schemaviolation_objects.first().filename == "failed_violation.xml"
    assert schemaviolation_objects.first().details == error_message


def test_run_task_post_schema_check(mocker, tmp_path, mock_post_schema_validator):
    """
    Given a zip file with an xml containing PII, violation
    entry will be recorded in table PostSchemaViolation table
    """

    file1 = tmp_path / "file1.xml"
    testzip = tmp_path / "test_pii.zip"
    create_text_file(
        file1,
        r'<TransXChange FileName="C:\Users\test\Documents\Marshalls of Sutton 2021-01-08 15-54\Marshalls of Sutton 55 2021-01-08 15-54.xml"></TransXChange',
    )
    create_zip_file(testzip, [file1])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="test_pii.zip"))

    zip_validator = TASK_MODULE + ".PostSchemaValidator"
    mocker.patch(
        zip_validator,
        return_value=mock_post_schema_validator,
    )
    task_post_schema_check(task.revision.id, task.id)

    postschemaviolation_objects = PostSchemaViolation.objects.filter(
        revision_id=task.revision.id
    )
    assert postschemaviolation_objects.count() == 1


def test_task_post_schema_check_zip_noviolation(
    mocker, tmp_path, mock_post_schema_validator_no_violation
):
    """
    Given a zip file with no PII violation, no violation
    will be recorded in PostSchemaViolation table
    """

    xml_file = DATA / "test_flexible_and_standard_service.xml"
    testzip = tmp_path / "testzip.zip"
    create_zip_file(testzip, [xml_file])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="testzip.zip"))

    zip_validator = TASK_MODULE + ".PostSchemaValidator"
    mocker.patch(
        zip_validator,
        return_value=mock_post_schema_validator_no_violation,
    )
    task_post_schema_check(task.revision.id, task.id)

    postschemaviolation_objects = PostSchemaViolation.objects.filter(
        revision_id=task.revision.id
    )
    assert postschemaviolation_objects.count() == 0


def test_run_task_post_schema_check_exception(
    mocker, tmp_path, mock_trans_xchange_dataset_parser
):
    """
    Given a zip file without any valid file, PipelineException is raised
    """

    file1 = tmp_path / "file1.xml"
    testzip = tmp_path / "test_pii.zip"
    create_text_file(
        file1,
        r'<TransXChange FileName="C:\Users\test\Documents\Marshalls of Sutton 2021-01-08 15-54\Marshalls of Sutton 55 2021-01-08 15-54.xml">',
    )
    create_zip_file(testzip, [file1])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="test_pii.zip"))

    zip_validator = TASK_MODULE + ".TransXChangeDatasetParser"
    mocker.patch(
        zip_validator,
        return_value=mock_trans_xchange_dataset_parser,
    )
    with pytest.raises(PipelineException) as exc_info:
        task_post_schema_check(task.revision.id, task.id)

    task.refresh_from_db()
    assert task.error_code == task.NO_VALID_FILE_TO_PROCESS


def test_antivirus_scan_suspicious_file_exception(mocker, tmp_path):
    """Given a suspicious file a PipelineException should be raised."""
    xml1 = tmp_path / "file1.xml"
    create_text_file(xml1, "<Root><Child>hello,world</Child></Root>")
    with open(xml1, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="file1.xml"))

    scanner = TASK_MODULE + ".FileScanner"
    scanner_obj = mocker.Mock(spec=FileScanner)
    scanner_obj.scan.side_effect = SuspiciousFile(task.revision.upload_file.name)
    mocker.patch(scanner, return_value=scanner_obj)

    with pytest.raises(PipelineException) as exc_info:
        task_scan_timetables(task.revision.id, task.id)

    task.refresh_from_db()
    expected = f"Anti-virus alert triggered for file {task.revision.upload_file.name}."
    assert task.error_code == task.SUSPICIOUS_FILE
    assert str(exc_info.value) == expected


def test_antivirus_scan_anti_virus_failure_exception(mocker, tmp_path):
    """Given an Exception a PipelineException should be raised."""
    xml1 = tmp_path / "file1.xml"
    create_text_file(xml1, "<Root><Child>hello,world</Child></Root>")
    with open(xml1, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="file1.xml"))

    scanner = TASK_MODULE + ".FileScanner"
    scanner_obj = mocker.Mock(spec=FileScanner)
    scanner_obj.scan.side_effect = AntiVirusError(task.revision.upload_file.name)
    mocker.patch(scanner, return_value=scanner_obj)

    with pytest.raises(PipelineException) as exc_info:
        task_scan_timetables(task.revision.id, task.id)

    task.refresh_from_db()
    expected = f"Antivirus failed validating file {task.revision.upload_file.name}."
    assert task.error_code == task.ANTIVIRUS_FAILURE
    assert str(exc_info.value) == expected


def test_file_check_general_exception(mocker):
    task = create_task(revision__upload_file__data=b"123")

    download_get = TASK_MODULE + ".TimetableFileValidator.validate"
    message = "A general exception"
    mocker.patch(download_get, side_effect=Exception(message))

    with pytest.raises(PipelineException) as exc_info:
        task_timetable_file_check(task.revision.id, task.id)

    task.refresh_from_db()
    assert task.error_code == task.SYSTEM_ERROR
    assert str(exc_info.value) == message


def test_task_pti_validation():
    upload_file_path = DATA / "3_pti_pass.zip"
    dataset = DatasetFactory(live_revision=None)
    revision = add_draft_revision(
        dataset,
        txc_version=2.2,
        upload_file__from_path=upload_file_path,
        status=FeedStatus.indexing.value,
    )
    TXCFileAttributesFactory(revision=revision)
    revision = dataset.revisions.first()

    task = revision.etl_results.first()
    task_pti_validation(revision.id, task.id)
    result = PTIValidationResult.objects.get(revision=revision)
    assert result.count == 0


def test_task_pti_validation_exception():
    """
    If there are no valid txcfile for the revision, PipelineException would be raised
    """
    upload_file_path = DATA / "3_pti_pass.zip"
    dataset = DatasetFactory(live_revision=None)
    revision = add_draft_revision(
        dataset,
        txc_version=2.2,
        upload_file__from_path=upload_file_path,
        status=FeedStatus.indexing.value,
    )
    revision = dataset.revisions.first()

    task = revision.etl_results.first()
    with pytest.raises(PipelineException) as exc_info:
        task_pti_validation(revision.id, task.id)
    task.refresh_from_db()
    assert task.error_code == task.NO_VALID_FILE_TO_PROCESS


def test_task_dataset_etl_exception():
    """
    If there are no valid txcfile for the revision, PipelineException would be raised
    """
    upload_file_path = DATA / "3_pti_pass.zip"
    dataset = DatasetFactory(live_revision=None)
    revision = add_draft_revision(
        dataset,
        txc_version=2.2,
        upload_file__from_path=upload_file_path,
        status=FeedStatus.indexing.value,
    )
    revision = dataset.revisions.first()

    task = revision.etl_results.first()
    with pytest.raises(PipelineException) as exc_info:
        task_dataset_etl(revision.id, task.id)
    task.refresh_from_db()
    assert task.error_code == task.NO_VALID_FILE_TO_PROCESS
