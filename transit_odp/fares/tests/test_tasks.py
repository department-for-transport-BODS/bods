import pytest
from django.core.files import File
from django.utils import timezone

from transit_odp.fares.extract import ExtractionError
from transit_odp.fares.tasks import task_run_fares_etl, task_run_fares_validation
from transit_odp.naptan.factories import StopPointFactory
from transit_odp.naptan.models import StopPoint
from transit_odp.organisation.constants import FeedStatus
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.validate import DownloadException, FileScanner
from transit_odp.validate.antivirus import SuspiciousFile
from transit_odp.validate.tests.utils import create_text_file, create_zip_file

pytestmark = pytest.mark.django_db


def create_task(**kwargs):
    """A helper function to return a DatasetETLTaskResult."""
    return DatasetETLTaskResultFactory(
        revision__status=FeedStatus.indexing.value,
        revision__is_published=False,
        revision__published_at=timezone.now(),
        status=DatasetETLTaskResult.STARTED,
        **kwargs,
    )


def test_task_run_fares_validation_no_task():
    """Given a task_id that doesn't exist, throw a PipelineException."""
    task_id = -1
    with pytest.raises(PipelineException) as exc_info:
        task_run_fares_validation(task_id)

    expected = f"DatasetETLTaskResult {task_id} does not exist."
    assert str(exc_info.value) == expected


def test_task_run_fares_validation_download_exception(mocker):
    download_get = "transit_odp.fares.tasks.DataDownloader.get"
    url_link = "http://fakeurl.com"
    task = create_task(revision__upload_file=None, revision__url_link=url_link)
    mocker.patch(download_get, side_effect=DownloadException(url_link))
    with pytest.raises(PipelineException) as exc_info:
        task_run_fares_validation(task.id)

    task.refresh_from_db()
    assert task.error_code == task.SYSTEM_ERROR
    assert str(exc_info.value) == f"Unable to download data from {url_link}."


def test_task_run_fares_validation_no_file_or_url():
    """Given task has no file or url_link."""
    task = create_task(revision__upload_file=None)
    with pytest.raises(PipelineException) as exc_info:
        task_run_fares_validation(task.id)

    expected = f"DatasetRevision {task.revision.id} doesn't contain a file."
    task.refresh_from_db()
    assert str(exc_info.value) == expected
    assert task.error_code == task.SYSTEM_ERROR


def test_validate_xml_files_from_zip_exception(tmp_path):
    """Given a zip file with an invalid xml a PipelineException is raised."""

    file1 = tmp_path / "file1.xml"
    testzip = tmp_path / "testzip.zip"
    create_text_file(file1, "not xml")
    create_zip_file(testzip, [file1])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="file1.xml"))

    with pytest.raises(PipelineException):
        task_run_fares_validation(task.id)

    task.refresh_from_db()
    assert task.error_code == task.XML_SYNTAX_ERROR


def test_xml_validation_error(tmp_path):
    """Given an invalid xml a PipelineException should be raised."""
    xml1 = tmp_path / "file1.xml"
    create_text_file(xml1, "<html></html>")
    with open(xml1, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="file1.xml"))

    with pytest.raises(PipelineException) as exc_info:
        task_run_fares_validation(task.id)

    task.refresh_from_db()
    expected = (
        "Element 'html': No matching global declaration available "
        "for the validation root."
    )
    assert task.error_code == task.XML_SYNTAX_ERROR
    assert str(exc_info.value) == expected


def test_antivirus_scan_exception(mocker, tmp_path):
    """Given a suspicious file a PipelineException should be raised."""
    xml1 = tmp_path / "file1.xml"
    create_text_file(xml1, "<Root><Child>hello,world</Child></Root>")
    with open(xml1, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="file1.xml"))

    scanner = "transit_odp.fares.tasks.FileScanner"
    scanner_obj = mocker.Mock(spec=FileScanner)
    scanner_obj.scan.side_effect = SuspiciousFile(task.revision.upload_file.name)
    mocker.patch(scanner, return_value=scanner_obj)

    validate = "transit_odp.fares.tasks.NeTExValidator.validate"
    mocker.patch(validate, return_value=None)

    with pytest.raises(PipelineException) as exc_info:
        task_run_fares_validation(task.id)

    task.refresh_from_db()
    expected = f"Anti-virus alert triggered for file {task.revision.upload_file.name}."
    assert task.error_code == task.SUSPICIOUS_FILE
    assert str(exc_info.value) == expected


def test_task_run_fares_etl_exception(mocker):
    extractor = "transit_odp.fares.tasks.NeTExDocumentsExtractor.__init__"
    msg = "Unable to extract metadata from file"
    mocker.patch(extractor, side_effect=ExtractionError(msg))

    get_docs = "transit_odp.fares.tasks.get_documents_from_file"
    mocker.patch(get_docs, return_value=[mocker.Mock()])

    task = create_task(revision__upload_file=None)
    with pytest.raises(PipelineException):
        task_run_fares_etl(task.id)

    task.refresh_from_db()
    assert task.error_code == task.SYSTEM_ERROR


def test_task_run_fares_etl(mocker, netexdocuments):
    StopPointFactory.create(id=1, atco_code="3290YYA00077")
    StopPointFactory.create(id=2, atco_code="3290YYA00359")
    StopPointFactory.create(id=3, atco_code="3290YYA01609")
    StopPointFactory.create(id=4, atco_code="3290YYA00103")

    get_docs = "transit_odp.fares.tasks.get_documents_from_file"
    mocker.patch(get_docs, return_value=netexdocuments)
    task = create_task(revision__upload_file=None)
    task_run_fares_etl(task.id)
    task.refresh_from_db()
    assert task.revision.metadata.faresmetadata.schema_version == "1.1"
    assert task.revision.metadata.faresmetadata.num_of_lines == 2
    assert task.revision.metadata.faresmetadata.num_of_fare_zones == 15
    assert list(task.revision.metadata.faresmetadata.stops.all()) == list(
        StopPoint.objects.all()
    )
