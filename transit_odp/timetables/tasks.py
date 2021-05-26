import zipfile
from logging import getLogger

import celery
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from transit_odp.common.loggers import PipelineAdapter
from transit_odp.data_quality.models import PTIObservation, SchemaViolation
from transit_odp.data_quality.tasks import upload_dataset_to_dqs
from transit_odp.fares.tasks import DT_FORMAT
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.organisation.models import DatasetRevision, TXCFileAttributes
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.etl import TransXChangePipeline
from transit_odp.timetables.loggers import RevisionLoggerContext, TaskLoggerContext
from transit_odp.timetables.transxchange import (
    TransXChangeDatasetParser,
    TransXChangeDocument,
    TransXChangeZip,
)
from transit_odp.timetables.updaters import TimetableUpdater
from transit_odp.timetables.utils import (
    get_available_remote_timetables,
    get_pti_validator,
    get_unavailable_remote_timetables,
)
from transit_odp.timetables.validate import (
    DatasetTXCValidator,
    TimetableFileValidator,
    TXCRevisionValidator,
)
from transit_odp.validate import (
    DataDownloader,
    DownloadException,
    FileScanner,
    ValidationException,
)

logger = getLogger(__name__)


@shared_task(bind=True)
def task_dataset_pipeline(self, revision_id: int, do_publish=False):
    context = RevisionLoggerContext(object_id=revision_id)
    adapter = PipelineAdapter(logger, {"context": context})
    adapter.info("Starting timetables pipeline.")
    try:
        revision = DatasetRevision.objects.get(id=revision_id)
    except DatasetRevision.DoesNotExist as e:
        adapter.exception("Object does not exist.")
        raise e
    else:
        with transaction.atomic():
            # TODO - refactor pipeline state to DatasetETLTaskResult
            # (then no need for transaction here)
            revision.to_indexing()
            revision.save()
            task = DatasetETLTaskResult.objects.create(
                revision=revision,
                status=DatasetETLTaskResult.STARTED,
                task_id=self.request.id,
            )

        jobs = [
            task_dataset_download.s(task.id),
            task_scan_timetables.s(task.id),
            task_dataset_validate.s(task.id),
            task_extract_txc_file_data.s(task.id),
            task_pti_validation.s(task.id),
            task_dqs_upload.s(task.id),
            task_dataset_etl.s(task.id),
            task_dataset_etl_finalise.s(task.id),
        ]

        if do_publish:
            jobs.append(task_publish_revision.si(revision_id))

        workflow = celery.chain(*jobs)
        return workflow.delay(revision.id)


def download_timetable(task_id):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Downloading data.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    if revision.url_link:
        adapter.info(f"Downloading timetables file from {revision.url_link}.")
        now = timezone.now().strftime(DT_FORMAT)
        try:
            downloader = DataDownloader(revision.url_link)
            response = downloader.get()
        except DownloadException as exc:
            logger.error(exc.message, exc_info=True)
            task.to_error("dataset_download", task.SYSTEM_ERROR)
            raise PipelineException(exc.message) from exc
        else:
            adapter.info("Timetables file downloaded successfully.")
            name = f"remote_dataset_{revision.dataset.id}_{now}.{response.filetype}"
            file_ = ContentFile(response.content, name=name)
    else:
        file_ = revision.upload_file

    revision.upload_file = file_
    revision.save()
    revision.refresh_from_db()
    task.update_progress(10)
    return revision


def run_scan_timetables(task_id: int):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Scanning file for viruses.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    try:
        scanner = FileScanner(settings.CLAMAV_HOST, settings.CLAMAV_PORT)
        scanner.scan(revision.upload_file)
    except ValidationException as exc:
        logger.error(exc.message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = exc.message
        task.save()
        raise PipelineException(exc.message) from exc
    except Exception as exc:
        message = str(exc)
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc

    task.update_progress(20)
    adapter.info("Scanning complete. No viruses.")
    return revision


def run_timetable_file_check(task_id: int):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Starting timetable file check.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    try:
        validator = TimetableFileValidator(revision=revision)
        validator.validate()
    except ValidationException as exc:
        message = exc.message
        logger.error(message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc
    except Exception as exc:
        message = str(exc)
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc

    task.update_progress(30)
    adapter.info("File check complete. No issues.")
    return revision


def run_timetable_txc_schema_validation(task_id: int):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})
    adapter.info("Starting timetable schema validation.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    # 'Update data' flow allows validation to occur multiple times
    # lets just delete any 'old' observations.
    revision.schema_violations.all().delete()
    revision.pti_observations.all().delete()

    try:
        adapter.info("Checking for violations.")
        validator = DatasetTXCValidator()
        violations = validator.get_violations(revision=revision)
    except Exception as exc:
        message = str(exc)
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SCHEMA_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc
    else:
        adapter.info(f"{len(violations)} violations found")
        if len(violations) > 0:
            schema_violations = [
                SchemaViolation.from_violation(revision_id=revision.id, violation=v)
                for v in violations
            ]
            SchemaViolation.objects.bulk_create(schema_violations)

            message = "TransXChange schema issues found."
            task.to_error("dataset_validate", DatasetETLTaskResult.SCHEMA_ERROR)
            task.additional_info = message
            task.save()
            raise PipelineException(message)

    task.update_progress(40)
    revision.save()
    adapter.info("Validation complete.")
    return revision


# TODO delete this function once schema violations are implemented
def validate_timetable(task_id: int):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Starting validation pipeline.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    if not revision.upload_file:
        task.to_error("dataset_validate", task.SYSTEM_ERROR)
        message = f"DatasetRevision {revision.id} doesn't contain a file."
        logger.error(message, exc_info=True)
        raise PipelineException(message)

    file_ = revision.upload_file
    try:
        if zipfile.is_zipfile(file_):
            adapter.info("Validating timetables zip file.")
            with TransXChangeZip(file_) as zip_:
                zip_.validate()
        else:
            adapter.info("Validating timetable TransXChange file.")
            TransXChangeDocument(file_)
    except ValidationException as exc:
        logger.error(exc.message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = exc.message
        task.save()
        raise PipelineException(exc.message) from exc

    task.update_progress(50)
    revision.save()
    adapter.info("Validation complete.")
    return revision


def run_txc_file_attribute_extraction(task_id: int):
    """
    Index the attributes and service code of every individual file in a dataset.
    """
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Extracting TXC attributes from individual files.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    try:
        # If we're in the update flow lets clear out "old" files.
        revision.txc_file_attributes.all().delete()
        parser = TransXChangeDatasetParser(revision.upload_file)
        headers = parser.get_file_headers()
        attributes = [
            TXCFileAttributes.from_txc_header(header=header, revision_id=revision.id)
            for header in headers
        ]
        TXCFileAttributes.objects.bulk_create(attributes)
        adapter.info(f"Attributes extracted from {len(headers)} files.")
    except Exception as exc:
        message = "An unexpected exception has occurred."
        adapter.error(str(exc), exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc


def run_pti_validation(task_id: int):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Starting PTI Profile validation.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    try:
        # 'Update data' flow allows validation to occur multiple times
        # lets just delete any 'old' observations.
        revision.pti_observations.all().delete()

        pti = get_pti_validator()
        violations = pti.get_violations(revision=revision)

        revision_validator = TXCRevisionValidator(revision)
        violations += revision_validator.get_violations()

        adapter.info(f"{len(violations)} violations found.")
        observations = [
            PTIObservation.from_violation(revision_id=revision.id, violation=v)
            for v in violations
        ]
        PTIObservation.objects.bulk_create(observations)

    except ValidationException as exc:
        message = "PTI Validation failed."
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc
    except Exception as exc:
        message = "An unexpected exception has occurred."
        adapter.error(str(exc), exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc

    task.update_progress(50)
    revision.save()
    adapter.info("Finished PTI Profile validation.")
    return revision


def run_timetable_etl_pipeline(task_id):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Starting ETL pipeline task.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    try:
        task.update_progress(60)
        pipeline = TransXChangePipeline(revision)
        extracted = pipeline.extract()
        adapter.info("Data successfully extracted.")
        task.update_progress(70)
        transformed = pipeline.transform(extracted)
        adapter.info("Data successfully transformed.")
        task.update_progress(80)
        pipeline.load(transformed)
        adapter.info("Data successfully loaded into BODS.")
        task.update_progress(90)
    except Exception as exc:
        message = "Unknown timetable ETL pipeline error."
        adapter.error(message, exc_info=True)
        task.to_error("dataset_etl", task.SYSTEM_ERROR)
        raise PipelineException(message) from exc

    adapter.info("Timetable ETL pipeline task completed.")
    return revision


def finalise_timetable_pipeline(task_id):
    context = TaskLoggerContext(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Finialising ETL pipeline.")
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    with transaction.atomic():
        task.to_success()
        task.update_progress(100)
        revision.to_success()
        revision.save()
    adapter.info("Timetable successfully processed.")


@shared_task(ignore_result=True)
def task_populate_timing_point_count(revision_id):
    try:
        revision = DatasetRevision.objects.get(id=revision_id)
    except DatasetRevision.DoesNotExist:
        return

    parser = TransXChangeDatasetParser(revision.upload_file)
    timing_point_count = len(parser.get_principal_timing_points())
    revision.num_of_timing_points = timing_point_count
    revision.save()


@shared_task()
def task_dataset_download(revision_id: int, task_id: int):
    """A task that downloads a dataset if a revision contains a url_link
    N.B. this is just a proxy to `download_timetable` as part of a refactor.
    """
    download_timetable(task_id)
    return revision_id


@shared_task
def task_scan_timetables(revision_id: int, task_id: int):
    run_scan_timetables(task_id=task_id)
    return revision_id


@shared_task()
def task_dataset_validate(revision_id: int, task_id: int):
    """A task that validates the file/s in a dataset."""
    run_timetable_file_check(task_id=task_id)
    run_timetable_txc_schema_validation(task_id=task_id)
    return revision_id


@shared_task()
def task_extract_txc_file_data(revision_id: int, task_id: int):
    run_txc_file_attribute_extraction(task_id)
    return revision_id


@shared_task()
def task_pti_validation(revision_id: int, task_id: int):
    run_pti_validation(task_id)
    return revision_id


@shared_task()
def task_dataset_etl(revision_id: int, task_id: int):
    """A task that runs the ETL pipeline on a timetable dataset.
    N.B. this is just a proxy to `run_timetable_etl_pipeline` as part of a refactor.
    """
    run_timetable_etl_pipeline(task_id)
    return revision_id


@shared_task()
def task_dqs_upload(revision_id: int, task_id: int):
    """A task that uploads a timetables dataset to the DQ Service.
    N.B. this is just a proxy to `upload_dataset_to_dqs` as part of a refactor.
    """
    upload_dataset_to_dqs(task_id)
    return revision_id


@shared_task()
def task_dataset_etl_finalise(revision_id: int, task_id: int):
    """A task that finalises a timetables dataset.
    N.B. this is just a proxy to `finalise_timetable_pipeline` as part of a refactor.
    """
    finalise_timetable_pipeline(task_id)


@shared_task(ignore_result=True)
def task_publish_revision(revision_id: int):
    # We use Celery to publish a revision automatically in the monitoring pipeline
    logger.info("task_publish_revision called with revision_id: %s" % revision_id)
    revision = DatasetRevision.objects.get(id=revision_id)
    if revision.status == "success" or revision.status == "error":
        revision.publish()


@shared_task(ignore_errors=True)
def task_update_remote_timetables():
    timetables = get_available_remote_timetables()
    logger.info(
        f"[TimetableMonitoring] Checking {timetables.count()} datasets for update."
    )
    for timetable in timetables:
        _prefix = f"[TimetableMonitoring] Dataset {timetable.id} => "
        logger.info(_prefix + "Checking for update.")
        try:
            updater = TimetableUpdater(timetable, task_dataset_pipeline)
            updater.update()
        except Exception:
            message = f"{_prefix} Failed to update timetable."
            logger.error(message, exc_info=True)


@shared_task(ignore_result=True)
def task_retry_unavailable_timetables():
    timetables = get_unavailable_remote_timetables()
    logger.info(
        f"[TimetableMonitoring] Checking {timetables.count()} datasets for update."
    )
    for timetable in timetables:
        _prefix = f"[TimetableMonitoring] Dataset {timetable.id} => "
        logger.info(_prefix + "Checking for update.")
        updater = TimetableUpdater(timetable, task_dataset_pipeline)
        updater.update()
