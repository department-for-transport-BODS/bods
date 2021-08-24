from unittest.mock import Mock

import pytest
from django.core.files import File
from django.utils import timezone
from freezegun import freeze_time
from requests import Response

from transit_odp.fares.tasks import DT_FORMAT
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.tasks import (
    download_timetable,
    run_scan_timetables,
    task_deactivate_txc_2_1,
    task_timetable_file_check,
    task_timetable_schema_check,
)
from transit_odp.users.factories import OrgAdminFactory
from transit_odp.validate import DownloadException, FileScanner
from transit_odp.validate.antivirus import SuspiciousFile
from transit_odp.validate.tests.utils import create_text_file, create_zip_file
from transit_odp.validate.xml import XMLSyntaxError

pytestmark = pytest.mark.django_db

TASK_MODULE = "transit_odp.timetables.tasks"


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
    txc_version = kwargs.get("txc_version", 2.1)
    status = kwargs.get("status", FeedStatus.live.value)
    is_published = kwargs.get("is_published", True)

    revision = DatasetRevisionFactory(
        transxchange_version=txc_version,
        dataset=dataset,
        status=status,
        is_published=is_published,
    )
    DatasetETLTaskResultFactory(revision=revision)


def add_live_revision(dataset, txc_version=2.1):
    _add_revision(dataset, txc_version=txc_version)


def add_draft_revision(dataset, txc_version=2.1):
    _add_revision(
        dataset,
        txc_version=txc_version,
        status=FeedStatus.success.value,
        is_published=False,
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
    with pytest.raises(PipelineException) as exc_info:
        download_timetable(task_id)

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
        download_timetable(task.id)
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
        download_timetable(task.id)

    task.refresh_from_db()
    assert task.error_code == task.SYSTEM_ERROR
    assert str(exc_info.value) == f"Unable to download data from {url_link}."


def test_download_timetable_no_file_or_url():
    """Given task has no file or url_link."""
    task = create_task(revision__upload_file=None)
    with pytest.raises(PipelineException) as exc_info:
        download_timetable(task.id)

    expected = f"DatasetRevision {task.revision.id} doesn't contain a file."
    task.refresh_from_db()
    assert str(exc_info.value) == expected
    assert task.error_code == task.SYSTEM_ERROR


def test_run_timetable_txc_schema_validation_exception(mocker, tmp_path):
    """Given a zip file with an invalid xml a PipelineException is raised."""

    file1 = tmp_path / "file1.xml"
    testzip = tmp_path / "testzip.zip"
    create_text_file(file1, "not xml")
    create_zip_file(testzip, [file1])
    with open(testzip, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="testzip.zip"))

    zip_validator = TASK_MODULE + ".DatasetTXCValidator"
    mocker.patch(
        zip_validator,
        side_effect=Exception("Exception thrown"),
    )
    with pytest.raises(PipelineException):
        task_timetable_schema_check(task.revision.id, task.id)

    task.refresh_from_db()
    assert task.error_code == task.SCHEMA_ERROR


def test_antivirus_scan_exception(mocker, tmp_path):
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
        run_scan_timetables(task.id)

    task.refresh_from_db()
    expected = f"Anti-virus alert triggered for file {task.revision.upload_file.name}."
    assert task.error_code == task.SUSPICIOUS_FILE
    assert str(exc_info.value) == expected


def test_antivirus_scan_general_exception(mocker, tmp_path):
    """Given an Exception a PipelineException should be raised."""
    xml1 = tmp_path / "file1.xml"
    create_text_file(xml1, "<Root><Child>hello,world</Child></Root>")
    with open(xml1, "rb") as zout:
        task = create_task(revision__upload_file=File(zout, name="file1.xml"))

    scanner = TASK_MODULE + ".FileScanner"
    scanner_obj = mocker.Mock(spec=FileScanner)
    message = "A general exception"
    scanner_obj.scan.side_effect = Exception(message)
    mocker.patch(scanner, return_value=scanner_obj)

    with pytest.raises(PipelineException) as exc_info:
        run_scan_timetables(task.id)

    task.refresh_from_db()
    assert task.error_code == task.SYSTEM_ERROR
    assert str(exc_info.value) == message


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


def test_file_check_validation_exception(mocker):
    task = create_task(revision__upload_file__data=b"123")

    download_get = TASK_MODULE + ".TimetableFileValidator.validate"
    filename = task.revision.upload_file.name
    mocker.patch(download_get, side_effect=XMLSyntaxError(filename=filename))

    with pytest.raises(PipelineException) as exc_info:
        task_timetable_file_check(task.revision.id, task.id)

    task.refresh_from_db()
    assert task.error_code == task.XML_SYNTAX_ERROR
    expected_message = XMLSyntaxError.message_template.format(filename=filename)
    assert str(exc_info.value) == expected_message


def test_single_dataset_with_one_live_revision(org_with_key_contact, mailoutbox):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    add_live_revision(dataset)

    task_deactivate_txc_2_1()
    fetched_revision = DatasetRevision.objects.get(id=dataset.live_revision.id)
    assert fetched_revision.status == FeedStatus.inactive.value
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to[0] == org_with_key_contact.key_contact.email
    assert email.subject == "[BODS] Your data set is no longer compliant"


def test_single_dataset_with_one_live_mixed_revision(org_with_key_contact, mailoutbox):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    add_live_revision(dataset, txc_version="2.1,2.4")

    task_deactivate_txc_2_1()
    fetched_revision = DatasetRevision.objects.get(id=dataset.live_revision.id)
    assert fetched_revision.status == FeedStatus.inactive.value
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to[0] == org_with_key_contact.key_contact.email
    assert email.subject == "[BODS] Your data set is no longer compliant"


def test_organisation_without_key_contact_doesnt_break():
    org = OrganisationFactory()
    dataset = DatasetFactory(live_revision=None, organisation=org)
    add_live_revision(dataset)

    task_deactivate_txc_2_1()
    fetched_revision = DatasetRevision.objects.get(id=dataset.live_revision.id)
    assert fetched_revision.status == FeedStatus.inactive.value


def test_draft_revision_without_task_doesnt_break(org_with_key_contact):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    DatasetRevisionFactory(
        dataset=dataset,
        transxchange_version=2.1,
        is_published=False,
        status=FeedStatus.success.value,
    )
    task_deactivate_txc_2_1()
    fetched_revision = DatasetRevision.objects.get(id=dataset.revisions.latest().id)
    assert fetched_revision.status == FeedStatus.error.value


def test_single_dataset_with_one_live_revision_and_one_draft(
    org_with_key_contact, mailoutbox
):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    add_live_revision(dataset)
    add_draft_revision(dataset)
    task_deactivate_txc_2_1()

    fetched_revision = DatasetRevision.objects.get(id=dataset.live_revision.id)
    assert dataset.revisions.count() == 1
    assert fetched_revision.status == FeedStatus.inactive.value
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to[0] == org_with_key_contact.key_contact.email
    assert email.subject == "[BODS] Your data set is no longer compliant"


def test_single_dataset_with_two_live_revisions(org_with_key_contact, mailoutbox):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    add_live_revision(dataset)
    add_live_revision(dataset)

    task_deactivate_txc_2_1()
    fetched_revision = DatasetRevision.objects.get(id=dataset.live_revision.id)
    assert dataset.revisions.count() == 2
    assert fetched_revision.status == FeedStatus.inactive.value
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to[0] == org_with_key_contact.key_contact.email
    assert email.subject == "[BODS] Your data set is no longer compliant"


def test_single_dataset_with_two_live_revisions_and_one_draft(
    org_with_key_contact, mailoutbox
):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    add_live_revision(dataset)
    add_live_revision(dataset)
    add_draft_revision(dataset)

    task_deactivate_txc_2_1()
    fetched_revision = DatasetRevision.objects.get(id=dataset.live_revision.id)
    assert dataset.revisions.count() == 2
    assert fetched_revision.status == FeedStatus.inactive.value
    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.to[0] == org_with_key_contact.key_contact.email
    assert email.subject == "[BODS] Your data set is no longer compliant"


def test_single_dataset_with_one_draft_revision(org_with_key_contact, mailoutbox):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    add_draft_revision(dataset)
    task_deactivate_txc_2_1()
    fetched_dataset = Dataset.objects.get(id=dataset.id)
    fetched_revision = fetched_dataset.revisions.latest()
    assert fetched_revision.status == FeedStatus.error.value
    assert not mailoutbox
    assert (
        fetched_revision.etl_results.latest().error_code
        == DatasetETLTaskResult.SCHEMA_ERROR
    )
    assert fetched_revision.schema_violations.first().filename == "transXchange.xml"


def test_single_dataset_with_one_mixed_draft_revision(org_with_key_contact):
    dataset = DatasetFactory(live_revision=None, organisation=org_with_key_contact)
    add_draft_revision(dataset, txc_version="2.4,2.1")
    task_deactivate_txc_2_1()
    fetched_dataset = Dataset.objects.get(id=dataset.id)
    fetched_revision = fetched_dataset.revisions.latest()
    assert fetched_revision.status == FeedStatus.error.value


def test_each_of_above_test_cases_at_once_5_datasets(org_with_key_contact, mailoutbox):
    d1, d2, d3, d4, d5 = create_datasets(org_with_key_contact)
    task_deactivate_txc_2_1()
    datasets = Dataset.objects.filter(id__in=[d1.id, d2.id, d3.id, d4.id])
    draft = Dataset.objects.get(id=d5.id)
    for dataset in datasets:
        assert dataset.live_revision.status == FeedStatus.inactive.value
    assert draft.revisions.latest().status == FeedStatus.error.value
    assert len(mailoutbox) == 1
    assert mailoutbox[0].body.count("Data set ID:") == 4


def test_5_organisations_with_5_datasets(mailoutbox):
    for _ in range(5):
        org = create_org_with_key_contact()
        create_datasets(org)

    task_deactivate_txc_2_1()
    assert len(mailoutbox) == 5
    for email in mailoutbox:
        assert email.body.count("Data set ID:") == 4

    # this also tests idempotency
    assert Organisation.objects.get_organisations_with_txc21_datasets().count() == 0


def test_mixture_of_txc2_1_and_txc2_4(mailoutbox):
    for _ in range(5):
        org = create_org_with_key_contact()
        create_datasets(org)
        create_datasets(org, txc_version=2.4)

    task_deactivate_txc_2_1()
    assert len(mailoutbox) == 5
    for email in mailoutbox:
        assert email.body.count("Data set ID:") == 4
    assert Organisation.objects.get_organisations_with_txc21_datasets().count() == 0

    for test_org in Organisation.objects.all():
        assert (
            test_org.dataset_set.filter(
                live_revision__status=FeedStatus.live.value
            ).count()
            == 4
        )
