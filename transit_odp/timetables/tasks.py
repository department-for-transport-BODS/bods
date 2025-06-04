import itertools
import uuid
import json
from logging import getLogger
from pathlib import Path
from urllib.parse import unquote
import time
import datetime

import celery
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone
from waffle import flag_is_active

from transit_odp.common.constants import CSVFileName
from transit_odp.common.loggers import (
    MonitoringLoggerContext,
    PipelineAdapter,
    get_dataset_adapter_from_revision,
)
from transit_odp.common.utils import sha1sum
from transit_odp.common.utils.aws_common import (
    SQSClientWrapper,
    StepFunctionsClientWrapper,
)
from transit_odp.common.utils.s3_bucket_connection import (
    get_file_name_by_id,
    read_datasets_file_from_s3,
)
from transit_odp.data_quality.models import SchemaViolation
from transit_odp.data_quality.models.report import (
    PostSchemaViolation,
    PTIObservation,
    PTIValidationResult,
)
from transit_odp.data_quality.tasks import update_dqs_task_status, upload_dataset_to_dqs
from transit_odp.dqs.models import Checks, Report, TaskResults
from transit_odp.fares.tasks import DT_FORMAT
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.organisation.constants import TimetableType, FeedStatus
from transit_odp.organisation.models import Dataset, DatasetRevision, TXCFileAttributes
from transit_odp.organisation.updaters import update_dataset
from transit_odp.pipelines.exceptions import NoValidFileToProcess, PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.dataclasses.transxchange import TXCFile
from transit_odp.timetables.etl import TransXChangePipeline
from transit_odp.timetables.proxies import TimetableDatasetRevision
from transit_odp.timetables.pti import get_pti_validator
from transit_odp.timetables.transxchange import TransXChangeDatasetParser
from transit_odp.timetables.utils import (
    create_queue_payload,
    get_bank_holidays,
    get_holidays_records_to_insert,
)
from transit_odp.timetables.validate import (
    DatasetTXCValidator,
    PostSchemaValidator,
    TimetableFileValidator,
    TXCRevisionValidator,
)
from transit_odp.transmodel.models import BankHolidays
from transit_odp.validate import (
    DataDownloader,
    DownloadException,
    FileScanner,
    ValidationException,
)
from transit_odp.publish.views.utils import (
    StepFunctionsTTPayload,
    S3Payload,
    InputDataSourceEnum,
)

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
            task_populate_original_file_hash.signature(args),
            task_timetable_schema_check.signature(args),
            task_post_schema_check.signature(args),
            task_extract_txc_file_data.signature(args),
            task_pti_validation.signature(args),
        ]

        if is_new_data_quality_service_active:
            jobs.append(task_dataset_etl.signature(args))
            jobs.append(task_data_quality_service.signature(args))
        else:
            jobs.append(task_dqs_upload.signature(args))
            jobs.append(task_dataset_etl.signature(args))

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
def task_dataset_download(
    revision_id: int, task_id: int, reprocess_flag: bool = False
) -> int:
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Downloading data.")
    if revision.url_link and not reprocess_flag:
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
        task.to_error("task_scan_timetables", exc.code)
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
    adapter.info("Checking for TXC schema violations.")
    validator = DatasetTXCValidator(revision=revision)
    violations = validator.get_violations()
    number_of_files_in_revision = validator.get_number_of_files_uploaded()
    adapter.info(f"{len(violations)} violations found")

    # 'Update data' flow allows validation to occur multiple times
    # lets just delete any 'old' observations irrespective of whether updated data has validations
    revision.schema_violations.all().delete()

    if number_of_files_in_revision > 0:
        if len(violations) > 0:
            schema_violations = [
                SchemaViolation.from_violation(revision_id=revision.id, violation=v)
                for v in violations
            ]

            with transaction.atomic():
                SchemaViolation.objects.bulk_create(
                    schema_violations, batch_size=BATCH_SIZE
                )
                revision.modify_upload_file(
                    list(set([sv.filename for sv in schema_violations]))
                )
        adapter.info("Validation complete.")
        task.update_progress(40)
    if number_of_files_in_revision == 0 or (
        len(violations) > 0 and revision.upload_file.name.endswith(".xml")
    ):
        message = f"Validation task: task_timetable_schema_check, no file to process, zip file: {revision.upload_file.name}"
        adapter.error(message, exc_info=True)
        task.to_error(
            "task_timetable_schema_check", DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS
        )
        task.additional_info = message
        task.save()
        raise PipelineException(message)
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
    violations = []
    parser = TransXChangeDatasetParser(revision.upload_file)
    doc_list = list(parser.get_documents())
    if not doc_list:
        message = f"Validation task: task_post_schema_check, no file to process, zip file: {revision.upload_file.name}"
        adapter.error(message, exc_info=True)
        task.to_error(
            "task_post_schema_check", DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS
        )
        task.additional_info = message
        task.save()
        raise PipelineException(message)

    validator = PostSchemaValidator(doc_list)
    violations += validator.get_violations()

    adapter.info(f"{len(violations)} violations found.")

    # 'Update data' flow allows validation to occur multiple times
    # lets just delete any 'old' observations irrespective of whether updated data has validations
    revision.post_schema_violations.all().delete()

    if len(violations) > 0:
        failed_filenames = validator.get_failed_validation_filenames()
        schema_violations = [
            PostSchemaViolation.from_violation(revision=revision, filename=filename)
            for filename in failed_filenames
        ]

        with transaction.atomic():
            PostSchemaViolation.objects.bulk_create(
                schema_violations, batch_size=BATCH_SIZE
            )
            revision.modify_upload_file([sv.filename for sv in schema_violations])
    adapter.info("Completed post schema validation check.")
    if len(violations) > 0 and revision.upload_file.name.endswith(".xml"):
        message = f"Validation task: task_post_schema_check, no file to process, zip file: {revision.upload_file.name}"
        adapter.error(message, exc_info=True)
        task.to_error(
            "task_post_schema_check", DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS
        )
        task.additional_info = message
        task.save()
        raise PipelineException(message)
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
        adapter.info(f"txc file attribute ETL has {len(files)} files to process")
        if not files:
            message = f"Validation task: task_extract_txc_file_data, no file to process, zip file: {revision.upload_file.name}"
            adapter.error(message, exc_info=True)
            task.to_error(
                "task_extract_txc_file_data",
                DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS,
            )
            task.additional_info = message
            task.save()
            raise PipelineException(message)

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

    valid_txc_files = list(
        TXCFileAttributes.objects.filter(revision=revision.id).values_list(
            "filename", flat=True
        )
    )
    adapter.info(f"PTI task has {len(valid_txc_files)} files to process")
    if not valid_txc_files:
        message = f"Validation task: task_pti_validation, no file to process, zip file: {revision.upload_file.name}"
        adapter.error(message, exc_info=True)
        task.to_error(
            "task_pti_validation", DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS
        )
        task.additional_info = message
        task.save()
        raise PipelineException(message)

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
        pti_violations = [
            PTIObservation.from_violation(revision_id=revision_id, violation=v)
            for v in violations
        ]
        PTIObservation.objects.bulk_create(pti_violations, batch_size=BATCH_SIZE)

        PTIValidationResult.objects.filter(revision_id=revision.id).delete()
        PTIValidationResult.from_pti_violations(
            revision=revision, violations=violations
        ).save()

        TXCFileAttributes.objects.filter(
            revision=revision.id, filename__in=[pv.filename for pv in pti_violations]
        ).delete()
        revision.modify_upload_file(list(set([pv.filename for pv in pti_violations])))
        task.update_progress(50)
        revision.save()

    adapter.info("Finished PTI Profile validation.")
    if len(violations) > 0 and revision.upload_file.name.endswith(".xml"):
        message = f"Validation task: task_pti_validation, no file to process, zip file: {revision.upload_file.name}"
        adapter.error(message, exc_info=True)
        task.to_error(
            "task_pti_validation", DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS
        )
        task.additional_info = message
        task.save()
        raise PipelineException(message)
    return revision_id


@shared_task()
def task_populate_original_file_hash(revision_id: int, task_id: int):
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = TimetableDatasetRevision.objects.get(id=revision_id)

    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    with revision.upload_file.open("rb") as f:
        original_hash = sha1sum(f.read())

    revision.original_file_hash = original_hash
    revision.save()

    return revision_id


@shared_task()
def task_dataset_etl(revision_id: int, task_id: int):
    """A task that runs the ETL pipeline on a timetable dataset.
    N.B. this is just a proxy to `run_timetable_etl_pipeline` as part of a refactor.
    """
    is_new_data_quality_service_active = flag_is_active(
        "", "is_new_data_quality_service_active"
    )
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)

    valid_txc_files = list(
        TXCFileAttributes.objects.filter(revision=revision.id).values_list(
            "filename", flat=True
        )
    )
    adapter.info(f"ETL task has {len(valid_txc_files)} files to process")
    if not valid_txc_files:
        message = f"ETL task: task_dataset_etl, no file to process, zip file: {revision.upload_file.name}"
        adapter.error(message, exc_info=True)
        task.to_error("task_dataset_etl", DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS)
        task.additional_info = message
        task.save()
        raise PipelineException(message)

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
    except NoValidFileToProcess as exp:
        message = f"Validation task: task_dataset_etl, no file to process, zip file: {revision.upload_file.name}"
        adapter.error(message, exc_info=True)
        task.to_error("task_dataset_etl", DatasetETLTaskResult.NO_VALID_FILE_TO_PROCESS)
        task.additional_info = message
        raise PipelineException(message)
    except Exception as exc:
        task.handle_general_pipeline_exception(
            exc,
            adapter,
            message="Unknown timetable ETL pipeline error.",
            task_name="dataset_etl",
        )
    if not is_new_data_quality_service_active:
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
    is_using_step_function_for_dqs = flag_is_active(
        "", "is_using_step_function_for_dqs"
    )

    """A task that runs the DQS checks on TxC file(s)."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    adapter = get_dataset_adapter_from_revision(logger=logger, revision=revision)
    adapter.info("Starting DQS checks initiation task.")
    try:
        task.update_progress(95)
        if is_using_step_function_for_dqs:
            adapter.info(f"Using state machine to run checks Txc files")
            step_function_client = StepFunctionsClientWrapper()
            input_payload = {"DatasetRevisionId": revision.id}
            execution_arn = step_function_client.start_step_function(
                json.dumps(input_payload),
                settings.DQS_STATE_MACHINE_ARN,
                f"DQSExecutionForRevision{revision.id}",
            )
            adapter.info(
                f"Began DQS State Machine Execution for {revision.id}: {execution_arn}"
            )
        else:
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
            adapter.info("DQS-SQS:SQS queue messages sent successfully.")

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
            csv_file_name = CSVFileName.DELETE_DATASETS.value
            _ids, _id_type = read_datasets_file_from_s3(csv_file_name)
            if not _ids and not _id_type == "dataset_ids":
                logger.info("No valid dataset IDs in the file.")
                return
            logger.info(f"Total number of datasets to be deleted is: {len(_ids)}")
            datasets = Dataset.objects.filter(id__in=_ids)
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
    csv_file_name = CSVFileName.RERUN_ETL_TIMETABLES.value
    _ids, _id_type, _s3_file_names_ids_map = read_datasets_file_from_s3(csv_file_name)

    if not _ids:
        logger.info("No valid dataset IDs or dataset revision IDs found in the file.")
        return

    timetables_datasets = []
    if _id_type == "dataset_id":
        logger.info(f"Total number of datasets to be processed: {len(_ids)}")
        timetables_datasets = Dataset.objects.filter(id__in=_ids).get_active()
    elif _id_type == "dataset_revision_id":
        logger.info(f"Total number of dataset revisions to be processed: {len(_ids)}")
        timetables_datasets = _ids

    if not timetables_datasets:
        logger.info("No active datasets found in BODS with these dataset IDs")
        return

    processed_count = 0
    successfully_processed_ids = []
    failed_datasets = []

    total_count = len(timetables_datasets)
    for timetables_dataset in timetables_datasets:
        try:
            if _id_type == "dataset_id":
                logger.info(
                    f"Running Timetables ETL pipeline for dataset id {timetables_dataset.id}"
                )
                revision = timetables_dataset.live_revision
                if revision:
                    revision_id = revision.id
                    output_id = revision.id
                else:
                    raise PipelineException(
                        f"No live revision for dataset id {timetables_dataset.id}"
                    )
            elif _id_type == "dataset_revision_id":
                revision_id = timetables_dataset
                output_id = timetables_dataset
                logger.info(
                    f"Running Timetables ETL pipeline for revision id {timetables_dataset}"
                )

            try:
                revision = DatasetRevision.objects.get(
                    pk=revision_id, dataset__dataset_type=TimetableType
                )
                if _s3_file_names_ids_map:
                    s3_file_name = get_file_name_by_id(
                        revision_id, _s3_file_names_ids_map
                    )
                    if s3_file_name:
                        revision.upload_file = s3_file_name
                        revision.save()

            except DatasetRevision.DoesNotExist as exc:
                message = f"DatasetRevision {revision_id} does not exist."
                logger.exception(message, exc_info=True)
                raise PipelineException(message) from exc

            if revision:
                task_id = uuid.uuid4()
                task = DatasetETLTaskResult.objects.create(
                    revision=revision,
                    status=DatasetETLTaskResult.STARTED,
                    task_id=task_id,
                )
                try:
                    task_dataset_download(revision_id, task.id, reprocess_flag=True)
                    task_populate_original_file_hash(revision_id, task.id)
                    task_extract_txc_file_data(revision_id, task.id)
                    task_dataset_etl(revision_id, task.id)

                    task.update_progress(100)
                    task.to_success()
                    successfully_processed_ids.append(output_id)
                    processed_count += 1
                    logger.info(
                        f"The task completed for {processed_count} of {total_count}"
                    )

                except Exception as e:
                    task.to_error("", DatasetETLTaskResult.FAILURE)
                    raise

        except Exception as exc:
            failed_datasets.append(output_id)
            message = f"Error processing dataset id {output_id}: {exc}"
            logger.exception(message, exc_info=True)

    logger.info(
        f"Total number of datasets processed successfully is {len(successfully_processed_ids)} out of {total_count}"
    )
    logger.info(
        f"The task failed to update {len(failed_datasets)} datasets with following ids: {failed_datasets}"
    )


class StepFunctionsReprocessPayload(StepFunctionsTTPayload):
    """
    Extends existing StepFunctionsTTPayload to allow addition of the performETLOnly flag
    which is only used for reprocessing
    """

    performETLOnly: bool


@shared_task(ignore_errors=True)
def task_rerun_timetables_serverless_etl_specific_datasets():
    """This is a one-off task to rerun the timetables ETL for a list of datasets
    provided in a csv file available in AWS S3 bucket using the serverless pipeline
    """
    csv_file_name = CSVFileName.RERUN_ETL_TIMETABLES.value
    _ids, _id_type, _s3_file_names_ids_map = read_datasets_file_from_s3(csv_file_name)

    if not _ids:
        logger.info(
            "Serverless reprocessing - no valid dataset IDs or dataset revision IDs found in the file."
        )
        return

    timetables_datasets = []
    if _id_type == "dataset_id":
        logger.info(
            f"Serverless reprocessing - total number of datasets to be processed: {len(_ids)}"
        )
        timetables_datasets = Dataset.objects.filter(id__in=_ids).get_active()
    elif _id_type == "dataset_revision_id":
        logger.info(
            f"Serverless reprocessing - total number of dataset revisions to be processed: {len(_ids)}"
        )
        timetables_datasets = _ids

    if not timetables_datasets:
        logger.info(
            "Serverless reprocessing - no active datasets found in BODS with these dataset IDs"
        )
        return

    processed_count = 0
    successfully_processed_ids = []
    failed_datasets = []

    total_count = len(timetables_datasets)
    for timetables_dataset in timetables_datasets:
        try:
            if _id_type == "dataset_id":
                logger.info(
                    f"Serverless reprocessing - running Timetables ETL pipeline for dataset id {timetables_dataset.id}"
                )
                revision = timetables_dataset.live_revision
                if revision:
                    revision_id = revision.id
                    output_id = revision.id
                else:
                    raise PipelineException(
                        f"Serverless reprocessing - no live revision for dataset id {timetables_dataset.id}"
                    )
            elif _id_type == "dataset_revision_id":
                revision_id = timetables_dataset
                output_id = timetables_dataset
                logger.info(
                    f"Serverless reprocessing - running Timetables ETL pipeline for revision id {timetables_dataset}"
                )

            try:
                revision = DatasetRevision.objects.get(
                    pk=revision_id, dataset__dataset_type=TimetableType
                )

                if revision.prepare_for_reprocessing():
                    logger.info(f"Revision {revision_id} prepared for reprocessing.")

                if _s3_file_names_ids_map:
                    s3_file_name = get_file_name_by_id(
                        revision_id, _s3_file_names_ids_map
                    )
                    if s3_file_name:
                        revision.upload_file = s3_file_name
                        revision.save()

            except DatasetRevision.DoesNotExist as exc:
                message = f"Serverless reprocessing - DatasetRevision {revision_id} does not exist."
                logger.exception(message, exc_info=True)
                raise PipelineException(message) from exc

            if revision:
                try:
                    task_id = uuid.uuid4()

                    with transaction.atomic():
                        if not revision.status == FeedStatus.pending.value:
                            revision.to_pending()
                            revision.save()
                        task = DatasetETLTaskResult.objects.create(
                            revision=revision,
                            status=DatasetETLTaskResult.STARTED,
                            task_id=task_id,
                        )
                    step_functions_client = StepFunctionsClientWrapper()
                    step_function_arn = settings.TIMETABLES_STATE_MACHINE_ARN

                    revision.txc_file_attributes.all().delete()
                    revision.num_of_lines = None
                    revision.admin_areas.clear()
                    revision.localities.clear()
                    revision.services.all().delete()
                    revision.service_patterns.all().delete()
                    revision.to_indexing()
                    revision.save()

                    payload = StepFunctionsReprocessPayload(
                        s3=S3Payload(object=revision.upload_file.name),
                        inputDataSource=InputDataSourceEnum.FILE_UPLOAD.value,
                        datasetRevisionId=revision_id,
                        datasetType="timetables",
                        publishDatasetRevision=False,
                        datasetETLTaskResultId=task.id,
                        performETLOnly=True,
                    ).model_dump_json(exclude_none=True)

                    step_functions_client.start_step_function(
                        payload, step_function_arn
                    )
                    logger.info(
                        f"Serverless reprocessing - successfully submitted Timetables ETL pipeline for revision id {timetables_dataset}"
                    )

                    while task.status not in [
                        DatasetETLTaskResult.SUCCESS,
                        DatasetETLTaskResult.FAILURE,
                        DatasetETLTaskResult.ERROR,
                    ]:
                        logger.info(
                            f"Serverless reprocessing - waiting on task completion for {timetables_dataset} - current status of task {task.id} is {task.status}"
                        )
                        time.sleep(30)
                        task.refresh_from_db()

                    # Check if there's been a failure or an error and set as error or else reset the revision status
                    if (
                        task.status == DatasetETLTaskResult.FAILURE
                        or task.status == DatasetETLTaskResult.ERROR
                    ):
                        task.to_error("", DatasetETLTaskResult.FAILURE)
                        raise
                    else:
                        revision.status = revision.status_before_reprocessing
                        revision.save()

                    while (
                        datetime.time(18, 30)
                        <= datetime.datetime.now().time()
                        <= datetime.time(19, 30)
                    ):
                        logger.info(
                            f"Serverless reprocessing - waiting for excluded time to finish for {timetables_dataset} - current status of task {task.id} is {task.status}"
                        )
                        time.sleep(60)

                    successfully_processed_ids.append(output_id)
                    processed_count += 1
                    logger.info(
                        f"Serverless reprocessing - The task completed for {processed_count} of {total_count}"
                    )

                except Exception as e:
                    task.to_error("", DatasetETLTaskResult.FAILURE)
                    raise

        except Exception as exc:
            failed_datasets.append(output_id)
            message = f"Error processing dataset id {output_id}: {exc}"
            logger.exception(message, exc_info=True)

    logger.info(
        f"Total number of datasets processed successfully is {len(successfully_processed_ids)} out of {total_count}"
    )
    logger.info(
        f"The task failed to update {len(failed_datasets)} datasets with following ids: {failed_datasets}"
    )


@shared_task(ignore_errors=True)
def task_rerun_timetables_dqs_specific_datasets():
    """This is a one-off task to rerun the timetables DQS task for a list of datasets
    provided in a csv file available in AWS S3 bucket
    """
    csv_file_name = CSVFileName.RERUN_DQS_TIMETABLES.value
    _ids, _id_type, _ = read_datasets_file_from_s3(csv_file_name)
    if not _ids:
        logger.info("No valid dataset IDs or dataset revision IDs found in the file.")
        return

    timetables_datasets = []
    if _id_type == "dataset_id":
        logger.info(f"Total number of datasets to be processed: {len(_ids)}")
        timetables_datasets = Dataset.objects.filter(id__in=_ids).get_active()
    elif _id_type == "dataset_revision_id":
        logger.info(f"Total number of dataset revisions to be processed: {len(_ids)}")
        timetables_datasets = _ids

    if not timetables_datasets:
        logger.info("No active datasets found in BODS with these dataset IDs")
        return

    processed_count = 0
    successfully_processed_ids = []
    failed_datasets = []

    total_count = len(timetables_datasets)
    for timetables_dataset in timetables_datasets:
        try:
            if _id_type == "dataset_id":
                logger.info(
                    f"Running Timetables DQS task for dataset id {timetables_dataset.id}"
                )
                revision = timetables_dataset.live_revision
                if revision:
                    revision_id = revision.id
                    output_id = revision.id
                else:
                    raise PipelineException(
                        f"No live revision for dataset id {timetables_dataset.id}"
                    )
            elif _id_type == "dataset_revision_id":
                revision_id = timetables_dataset
                output_id = timetables_dataset
                logger.info(
                    f"Running Timetables DQS task for revision id {timetables_dataset}"
                )

            try:
                revision = DatasetRevision.objects.get(
                    pk=revision_id, dataset__dataset_type=TimetableType
                )

            except DatasetRevision.DoesNotExist as exc:
                message = f"DatasetRevision {revision_id} does not exist."
                logger.exception(message, exc_info=True)
                raise PipelineException(message) from exc

            if revision:
                task_id = uuid.uuid4()
                task = DatasetETLTaskResult.objects.create(
                    revision=revision,
                    status=DatasetETLTaskResult.STARTED,
                    task_id=task_id,
                )
                try:
                    task_data_quality_service(revision_id, task.id)

                    task.update_progress(100)
                    task.to_success()
                    successfully_processed_ids.append(output_id)
                    processed_count += 1
                    logger.info(
                        f"The task completed for {processed_count} of {total_count}"
                    )

                except Exception as e:
                    task.to_error("", DatasetETLTaskResult.FAILURE)
                    raise

        except Exception as exc:
            failed_datasets.append(output_id)
            message = f"Error processing dataset id {output_id}: {exc}"
            logger.exception(message, exc_info=True)

    logger.info(
        f"Total number of datasets processed successfully is {len(successfully_processed_ids)} out of {total_count}"
    )
    logger.info(
        f"The task failed to update {len(failed_datasets)} datasets with following ids: {failed_datasets}"
    )
