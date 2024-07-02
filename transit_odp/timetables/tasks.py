import uuid

from logging import getLogger
from pathlib import Path
from urllib.parse import unquote

import celery
import itertools
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone
from waffle import flag_is_active

from transit_odp.common.loggers import (
    MonitoringLoggerContext,
    PipelineAdapter,
    get_dataset_adapter_from_revision,
)
from transit_odp.data_quality.models import SchemaViolation
from transit_odp.data_quality.models.report import (
    PostSchemaViolation,
    PTIValidationResult,
)
from transit_odp.data_quality.tasks import upload_dataset_to_dqs, update_dqs_task_status
from transit_odp.fares.tasks import DT_FORMAT
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.organisation.models import Dataset, DatasetRevision, TXCFileAttributes
from transit_odp.organisation.updaters import update_dataset
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.dataclasses.transxchange import TXCFile
from transit_odp.timetables.etl import TransXChangePipeline
from transit_odp.timetables.proxies import TimetableDatasetRevision
from transit_odp.timetables.pti import get_pti_validator
from transit_odp.timetables.transxchange import TransXChangeDatasetParser
from transit_odp.timetables.utils import (
    get_bank_holidays,
    get_holidays_records_to_insert,
    create_queue_payload,
)
from transit_odp.common.utils.s3_bucket_connection import read_datasets_file_from_s3
from transit_odp.organisation.constants import TimetableType
from transit_odp.timetables.validate import (
    DatasetTXCValidator,
    PostSchemaValidator,
    TimetableFileValidator,
    TXCRevisionValidator,
)
from transit_odp.transmodel.models import BankHolidays
from transit_odp.dqs.models import Report, Checks, TaskResults
from transit_odp.validate import (
    DataDownloader,
    DownloadException,
    FileScanner,
    ValidationException,
)
from transit_odp.common.utils.aws_common import SQSClientWrapper

logger = getLogger(__name__)

BATCH_SIZE = 2000


@shared_task(bind=True)
def task_dataset_pipeline(self, revision_id: int, do_publish=False):
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )

    try:
        revision = DatasetRevision.objects.get(id=revision_id)
    except DatasetRevision.DoesNotExist as e:
        raise e
    else:
        adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
        adapter.info("Starting timetables pipeline.")
        with transaction.atomic():
            revision.to_indexing()
            revision.save()
            task = DatasetETLTaskResult.objects.create(
                revision=revision,
                status=DatasetETLTaskResult.STARTED,
                task_id=self.request.id,
            )

        adapter.info(f"Dataset {revision.dataset_id} - task {task.id}")
        args = (task.id,)

        jobs = [
            task_dataset_download.signature(args),
            task_scan_timetables.signature(args),
            task_timetable_file_check.signature(args),
            task_timetable_schema_check.signature(args),
            task_post_schema_check.signature(args),
            task_extract_txc_file_data.signature(args),
            task_pti_validation.signature(args),
            task_dqs_upload.signature(args),
            task_dataset_etl.signature(args),
        ]

        if is_new_data_quality_service_active:
            jobs.append(task_data_quality_service.signature(args))

        # Adding the final step for ETL
        jobs.append(task_dataset_etl_finalise.signature(args))

        if do_publish:
            jobs.append(task_publish_revision.signature((revision_id,), immutable=True))

        workflow = celery.chain(*jobs)
        return workflow.delay(revision.id)


@shared_task(ignore_result=True)
def task_populate_timing_point_count(revision_id: int) -> None:
    try:
        revision = DatasetRevision.objects.get(id=revision_id)
    except DatasetRevision.DoesNotExist:
        return

    parser = TransXChangeDatasetParser(revision.upload_file)
    timing_point_count = len(parser.get_principal_timing_points())
    revision.num_of_timing_points = timing_point_count
    revision.save()


@shared_task()
def task_dataset_download(revision_id: int, task_id: int) -> int:
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Downloading data.")
    if revision.url_link:
        adapter.info(f"Downloading timetables file from {revision.url_link}.")
        now = timezone.now().strftime(DT_FORMAT)
        try:
            downloader = DataDownloader(revision.url_link)
            response = downloader.get()
        except DownloadException as exc:
            adapter.error(exc.message, exc_info=True)
            task.to_error("dataset_download", task.SYSTEM_ERROR)
            raise PipelineException(exc.message) from exc
        else:
            adapter.info("Timetables file downloaded successfully.")

            url_path = Path(revision.url_link)
            if url_path.suffix in (".zip", ".xml"):
                name = unquote(url_path.name)
            else:
                name = f"remote_dataset_{revision.dataset.id}_{now}.{response.filetype}"
            file_ = ContentFile(response.content, name=name)
            revision.upload_file = file_
            revision.save()
            revision.refresh_from_db()

    if not revision.upload_file:
        message = f"DatasetRevision {revision.id} doesn't contain a file."
        adapter.error(message, exc_info=True)
        task.to_error("dataset_download", task.SYSTEM_ERROR)
        raise PipelineException(message=message)

    task.update_progress(10)
    return revision_id


@shared_task()
def task_scan_timetables(revision_id: int, task_id: int) -> int:
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Scanning file for viruses.")
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
        task.handle_general_pipeline_exception(exc, adapter)

    task.update_progress(20)
    adapter.info("Scanning complete. No viruses.")
    return revision_id


@shared_task(acks_late=True)
def task_timetable_file_check(revision_id: int, task_id: int) -> int:
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = DatasetRevision.objects.get(id=revision_id)

    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Starting timetable file check.")
    try:
        validator = TimetableFileValidator(revision=revision)
        validator.validate()
        task.update_progress(30)
        adapter.info("File check complete. No issues.")
    except ValidationException as exc:
        message = exc.message
        logger.error(message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc
    except Exception as exc:
        task.handle_general_pipeline_exception(exc, adapter)

    return revision_id


@shared_task(acks_late=True)
def task_timetable_schema_check(revision_id: int, task_id: int):
    """A task that validates the file/s in a dataset."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = DatasetRevision.objects.get(id=revision_id)
    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Starting timetable schema validation.")

    try:
        adapter.info("Checking for TXC schema violations.")
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

            with transaction.atomic():
                # 'Update data' flow allows validation to occur multiple times
                # lets just delete any 'old' observations.
                revision.schema_violations.all().delete()
                SchemaViolation.objects.bulk_create(
                    schema_violations, batch_size=BATCH_SIZE
                )

                message = "TransXChange schema issues found."
                task.to_error("dataset_validate", DatasetETLTaskResult.SCHEMA_ERROR)
                task.additional_info = message
                task.save()
            raise PipelineException(message)
        else:
            adapter.info("Validation complete.")
            task.update_progress(40)
            return revision_id


@shared_task
def task_post_schema_check(revision_id: int, task_id: int):
    """
    Post schema checks, such as personal identifiable information (PII),
    publishing an already active dataset, and adding a service that
    doesn't belong to your organisation.
    """
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = DatasetRevision.objects.get(id=revision_id)
    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Starting post schema validation check.")

    try:
        violations = []
        parser = TransXChangeDatasetParser(revision.upload_file)
        file_names_list = parser.get_file_names()
        validator = PostSchemaValidator(file_names_list)
        violations += validator.get_violations()
    except Exception as exc:
        message = "TransXChange post schema issues found."
        adapter.error(message, exc_info=True)
        task.to_error(
            "post_schema_dataset_validate", DatasetETLTaskResult.POST_SCHEMA_ERROR
        )
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc
    else:
        adapter.info(f"{len(violations)} violations found.")
        if len(violations) > 0:
            schema_violations = [
                PostSchemaViolation.from_violation(revision=revision, violation=v)
                for v in violations
            ]

            with transaction.atomic():
                # 'Update data' flow allows validation to occur multiple times
                revision.post_schema_violations.all().delete()
                PostSchemaViolation.objects.bulk_create(
                    schema_violations, batch_size=BATCH_SIZE
                )

                message = "TransXChange post schema issues found."
                task.to_error(
                    "post_schema_dataset_validate",
                    DatasetETLTaskResult.POST_SCHEMA_ERROR,
                )
                task.additional_info = message
                task.save()
            raise PipelineException(message)
        else:
            adapter.info("Completed post schema validation check.")
            return revision_id


@shared_task()
def task_extract_txc_file_data(revision_id: int, task_id: int):
    """
    Index the attributes and service code of every individual file in a dataset.
    """
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Extracting TXC attributes from individual files.")
    try:
        # If we're in the update flow lets clear out "old" files.
        revision.txc_file_attributes.all().delete()
        parser = TransXChangeDatasetParser(revision.upload_file)
        files = [
            TXCFile.from_txc_document(doc, use_path_filename=True)
            for doc in parser.get_documents()
        ]

        attributes = [
            TXCFileAttributes.from_txc_file(txc_file=f, revision_id=revision.id)
            for f in files
        ]
        TXCFileAttributes.objects.bulk_create(attributes, batch_size=BATCH_SIZE)
        adapter.info(f"Attributes extracted from {len(attributes)} files.")
    except Exception as exc:
        task.handle_general_pipeline_exception(
            exc, adapter, message="An unexpected exception has occurred."
        )

    task.update_progress(45)
    return revision_id


@shared_task(acks_late=True)
def task_pti_validation(revision_id: int, task_id: int):
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = TimetableDatasetRevision.objects.get(id=revision_id)

    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Starting PTI Profile validation.")
    try:
        pti = get_pti_validator()
        violations = pti.get_violations(revision=revision)
        revision_validator = TXCRevisionValidator(revision)
        violations += revision_validator.get_violations()
        adapter.info(f"{len(violations)} violations found.")

        with transaction.atomic():
            # 'Update data' flow allows validation to occur multiple times
            # lets just delete any 'old' observations.
            # TODO remove once pti observations have been transitioned to pti results
            revision.pti_observations.all().delete()
            PTIValidationResult.objects.filter(revision_id=revision.id).delete()
            PTIValidationResult.from_pti_violations(
                revision=revision, violations=violations
            ).save()
            task.update_progress(50)
            revision.save()
    except ValidationException as exc:
        message = "PTI Validation failed."
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc
    except Exception as exc:
        task.handle_general_pipeline_exception(exc, adapter)

    if settings.PTI_ENFORCED_DATE.date() <= timezone.localdate() and violations:
        message = "PTI Validation failed."
        adapter.error(message)
        task.to_error("dataset_validate", ValidationException.code)
        task.additional_info = message
        task.save()
        raise PipelineException(message)

    adapter.info("Finished PTI Profile validation.")
    return revision_id


@shared_task()
def task_dataset_etl(revision_id: int, task_id: int):
    """A task that runs the ETL pipeline on a timetable dataset.
    N.B. this is just a proxy to `run_timetable_etl_pipeline` as part of a refactor.
    """
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Starting ETL pipeline task.")
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
        task.handle_general_pipeline_exception(
            exc,
            adapter,
            message="Unknown timetable ETL pipeline error.",
            task_name="dataset_etl",
        )
    update_dqs_task_status(task_id)
    adapter.info("Timetable ETL pipeline task completed.")
    return revision_id


@shared_task()
def task_dqs_upload(revision_id: int, task_id: int):
    """A task that uploads a timetables dataset to the DQ Service.
    N.B. this is just a proxy to `upload_dataset_to_dqs` as part of a refactor.
    """
    upload_dataset_to_dqs(task_id)


@shared_task()
def task_data_quality_service(revision_id: int, task_id: int) -> int:
    """A task that runs the DQS checks on TxC file(s)."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Starting DQS checks initiation task.")
    try:
        task.update_progress(95)
        report = Report.initialise_dqs_task(revision)
        adapter.info(
            f"Report is initialised for with status PIPELINE_PENDING for {revision}"
        )
        checks = Checks.get_all_checks()
        txc_file_attributes_objects = TXCFileAttributes.objects.for_revision(
            revision.id
        )
        combinations = itertools.product(txc_file_attributes_objects, checks)
        TaskResults.initialize_task_results(report, combinations)
        adapter.info(
            f"TaskResults is initialised for with status PENDING for {revision}"
        )
        pending_checks = TaskResults.objects.get_pending_objects(
            txc_file_attributes_objects
        )
        adapter.info(
            f"DQS-SQS:The number of pending check items is: {len(pending_checks)}"
        )
        queues_payload = create_queue_payload(pending_checks)
        sqs_queue_client = SQSClientWrapper()
        sqs_queue_client.send_message_to_queue(queues_payload)
        adapter.info("DQS-SQS:SQS queue messsages sent successfully.")

    except (DatabaseError, IntegrityError) as db_exc:
        task.handle_general_pipeline_exception(
            db_exc,
            adapter,
            message="Database error occurred:",
            task_name="dataset_etl",
        )

    except Exception as exc:
        task.handle_general_pipeline_exception(
            exc,
            adapter,
            message="Unknown timetable pipeline error in DQS.",
            task_name="dataset_etl",
        )
    adapter.info("Timetable DQS initiation task completed.")
    return revision_id


@shared_task()
def task_dataset_etl_finalise(revision_id: int, task_id: int) -> int:
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Finalising Timetable.")
    with transaction.atomic():
        task.to_success()
        task.update_progress(100)
        revision.to_success()
        revision.save()
    adapter.info("Timetable successfully processed.")
    return revision_id


@shared_task(ignore_result=True)
def task_publish_revision(revision_id: int) -> None:
    # We use Celery to publish a revision automatically in the monitoring pipeline
    logger.info("task_publish_revision called with revision_id: %s" % revision_id)
    revision = DatasetRevision.objects.get(id=revision_id)
    if revision.status == "success" or revision.status == "error":
        revision.publish()


@shared_task(ignore_errors=True)
def task_update_remote_timetables() -> None:
    timetables = Dataset.objects.get_available_remote_timetables()
    context = MonitoringLoggerContext(object_id=0)
    adapter = PipelineAdapter(logger, {"context": context})
    count = timetables.count()
    adapter.info(f"{count} datasets to check.")
    for timetable in timetables:
        update_dataset(timetable, task_dataset_pipeline)


@shared_task(ignore_result=True)
def task_retry_unavailable_timetables() -> None:
    timetables = Dataset.objects.get_unavailable_remote_timetables()
    context = MonitoringLoggerContext(object_id=-1)
    adapter = PipelineAdapter(logger, {"context": context})
    count = timetables.count()
    adapter.info(f"{count} datasets to check.")
    for timetable in timetables:
        update_dataset(timetable, task_dataset_pipeline)


@shared_task()
def task_log_stuck_revisions() -> None:
    revisions = DatasetRevision.objects.get_stuck_revisions().order_by("created")
    logger.info(f"There are {revisions.count()} revisions stuck in processing.")
    for revision in revisions:
        logger.info(f"Dataset {revision.dataset_id} => Revision is stuck.")


@shared_task()
def task_delete_datasets(*args):
    """This is a one-off task to delete datasets from BODS database
    If a dataset ID is provided as an argument, use it for deletion or proceed
    with the file in S3 bucket
    """

    if len(args) > 1:
        logger.error(
            "Too many arguments provided. This task expects only one dataset_id."
        )
        return

    dataset_id = args[0] if args else None

    if dataset_id is not None:
        try:
            dataset = Dataset.objects.get(id=dataset_id)
            try:
                dataset.delete()
                logger.info(f"Deleted dataset with ID: {dataset_id}")
            except IntegrityError as e:
                logger.error(f"Error deleting dataset {dataset_id}: {str(e)}")
        except Dataset.DoesNotExist:
            logger.warning(f"Dataset with ID {dataset_id} does not exist.")
    else:
        try:
            csv_file_name = "delete_datasets.csv"
            dataset_ids = read_datasets_file_from_s3(csv_file_name)
            if not dataset_ids:
                logger.info("No valid dataset IDs found in the file.")
                return
            logger.info(
                f"Total number of datasets to be deleted is: {len(dataset_ids)}"
            )
            datasets = Dataset.objects.filter(id__in=dataset_ids)
            deleted_count = 0
            failed_deletion_ids = []

            for dataset in datasets:
                try:
                    dataset.delete()
                    deleted_count += 1
                except IntegrityError as e:
                    logger.error(f"Error deleting dataset {dataset.id}: {str(e)}")
                    failed_deletion_ids.append(dataset.id)

            logger.info(f"Total number of datasets deleted is: {deleted_count}")
            if failed_deletion_ids:
                logger.error(
                    f"Failed to delete datasets with IDs: {failed_deletion_ids}"
                )
        except Exception as e:
            logger.warning(
                f"Error reading or processing the delete datasets file: {str(e)}"
            )
            return []


@shared_task()
def task_load_bank_holidays():
    """This is a task to load bank holidays from api to BODS database"""
    logger.info("Starting process to load bank holidays from api")
    bank_holidays = get_bank_holidays()
    logger.info("completed process to load bank holidays from api successfully")
    bank_holidays_to_insert = list(get_holidays_records_to_insert(bank_holidays))
    with transaction.atomic():
        BankHolidays.objects.all().delete()
        BankHolidays.objects.bulk_create(bank_holidays_to_insert, BATCH_SIZE)
        logger.info("completed process to load bank holidays from api successfully")


@shared_task(ignore_errors=True)
def task_rerun_timetables_etl_specific_datasets():
    """This is a one-off task to rerun the timetables ETL for a list of datasets
    provided in a csv file available in AWS S3 bucket
    """
    csv_file_name = "rerun_timetables_etl.csv"
    dataset_ids = read_datasets_file_from_s3(csv_file_name)
    if not dataset_ids:
        logger.info("No valid dataset IDs found in the file.")
        return
    logger.info(f"Total number of datasets to be processed: {len(dataset_ids)}")
    timetables_datasets = Dataset.objects.filter(id__in=dataset_ids).get_active()

    if not timetables_datasets:
        logger.info(f"No active datasets found in BODS with these dataset IDs")
        return

    processed_count = 0
    successfully_processed_ids = []
    failed_datasets = []

    total_count = timetables_datasets.count()
    for timetables_dataset in timetables_datasets:
        try:
            logger.info(
                f"Running Timetables ETL pipeline for dataset id {timetables_dataset.id}"
            )
            revision = timetables_dataset.live_revision
            if revision:
                revision_id = revision.id
                try:
                    revision = DatasetRevision.objects.get(
                        pk=revision_id, dataset__dataset_type=TimetableType
                    )
                except DatasetRevision.DoesNotExist as exc:
                    message = f"DatasetRevision {revision_id} does not exist."
                    failed_datasets.append(timetables_dataset.id)
                    logger.exception(message, exc_info=True)
                    raise PipelineException(message) from exc

                task_id = uuid.uuid4()
                task = DatasetETLTaskResult.objects.create(
                    revision=revision,
                    status=DatasetETLTaskResult.STARTED,
                    task_id=task_id,
                )

                task_dataset_download(revision_id, task.id)
                task_dataset_etl(revision_id, task.id)

                task.update_progress(100)
                task.to_success()
                successfully_processed_ids.append(timetables_dataset.id)
                processed_count += 1
                logger.info(
                    f"The task completed for {processed_count} of {total_count}"
                )

        except Exception as exc:
            failed_datasets.append(timetables_dataset.id)
            message = f"Error processing dataset id {timetables_dataset.id}: {exc}"
            logger.exception(message, exc_info=True)

    logger.info(
        f"Total number of datasets processed successfully is {len(successfully_processed_ids)} out of {total_count}"
    )
    logger.info(
        f"The task failed to update {len(failed_datasets)} datasets with following ids: {failed_datasets}"
    )
