from logging import getLogger
from pathlib import Path
from urllib.parse import unquote

import celery
import pytz
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models.query_utils import Q
from django.utils import timezone

from transit_odp.common.loggers import (
    MonitoringLoggerContext,
    PipelineAdapter,
    get_dataset_adapter_from_revision,
)
from transit_odp.data_quality.models import SchemaViolation
from transit_odp.data_quality.models.report import PTIValidationResult
from transit_odp.data_quality.tasks import upload_dataset_to_dqs
from transit_odp.fares.tasks import DT_FORMAT
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.organisation.constants import FeedStatus, TimetableType
from transit_odp.organisation.models import (
    Dataset,
    DatasetRevision,
    Organisation,
    TXCFileAttributes,
)
from transit_odp.organisation.updaters import update_dataset
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.constants import PTI_COMMENT, TXC_21
from transit_odp.timetables.dataclasses.transxchange import TXCFile
from transit_odp.timetables.etl import TransXChangePipeline
from transit_odp.timetables.notifications import (
    send_data_no_longer_compliant_notification,
)
from transit_odp.timetables.pti import get_pti_validator
from transit_odp.timetables.transxchange import TransXChangeDatasetParser
from transit_odp.timetables.updaters import reprocess_live_revision
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

BATCH_SIZE = 10000

logger = getLogger(__name__)

BATCH_SIZE = 25_000


@shared_task(bind=True)
def task_dataset_pipeline(self, revision_id: int, do_publish=False):
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
            task_extract_txc_file_data.signature(args),
            task_pti_validation.signature(args),
            task_dqs_upload.signature(args),
            task_dataset_etl.signature(args),
            task_dataset_etl_finalise.signature(args),
        ]

        if do_publish:
            jobs.append(task_publish_revision.signature((revision_id,), immutable=True))

        workflow = celery.chain(*jobs)
        return workflow.delay(revision.id)


def download_timetable(task_id):
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
    return revision


def run_scan_timetables(task_id: int):
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
        message = str(exc)
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc

    task.update_progress(20)
    adapter.info("Scanning complete. No viruses.")
    return revision


def run_txc_file_attribute_extraction(task_id: int):
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
        message = "An unexpected exception has occurred."
        adapter.error(str(exc), exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc

    task.update_progress(45)


def run_timetable_etl_pipeline(task_id):
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
        message = "Unknown timetable ETL pipeline error."
        adapter.error(message, exc_info=True)
        task.to_error("dataset_etl", task.SYSTEM_ERROR)
        raise PipelineException(message) from exc

    adapter.info("Timetable ETL pipeline task completed.")
    return revision


def finalise_timetable_pipeline(task_id):
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


@shared_task()
def task_scan_timetables(revision_id: int, task_id: int):
    run_scan_timetables(task_id=task_id)
    return revision_id


@shared_task(bind=True, acks_late=True)
def task_timetable_file_check(self, revision_id: int, task_id: int):
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
        message = str(exc)
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc

    return revision_id


@shared_task(bind=True, acks_late=True)
def task_timetable_schema_check(self, revision_id: int, task_id: int):
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


@shared_task(bind=True)
def task_extract_txc_file_data(self, revision_id: int, task_id: int):
    run_txc_file_attribute_extraction(task_id)
    return revision_id


@shared_task(bind=True, acks_late=True)
def task_pti_validation(self, revision_id: int, task_id: int):
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = DatasetRevision.objects.get(id=revision_id)

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
        message = str(exc)
        adapter.error(message, exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
        task.additional_info = message
        task.save()
        raise PipelineException(message) from exc

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
    timetables = Dataset.objects.get_available_remote_timetables()
    context = MonitoringLoggerContext(object_id=0)
    adapter = PipelineAdapter(logger, {"context": context})
    count = timetables.count()
    adapter.info(f"{count} datasets to check.")
    for timetable in timetables:
        update_dataset(timetable, task_dataset_pipeline)


@shared_task(ignore_result=True)
def task_retry_unavailable_timetables():
    timetables = Dataset.objects.get_unavailable_remote_timetables()
    context = MonitoringLoggerContext(object_id=-1)
    adapter = PipelineAdapter(logger, {"context": context})
    count = timetables.count()
    adapter.info(f"{count} datasets to check.")
    for timetable in timetables:
        update_dataset(timetable, task_dataset_pipeline)


@shared_task()
def task_deactivate_txc_2_1():
    organisations = Organisation.objects.get_organisations_with_txc21_datasets()
    count = organisations.count()
    logger.info(f"{count} organisations with active txc 2.1 datasets to deactivate")
    for organisation in organisations:
        deactivate_txc21_published_datasets(organisation)
        error_txc21_draft_datasets(organisation)


def deactivate_txc21_published_datasets(organisation: Organisation):
    published_datasets = organisation.dataset_set.select_related(
        "live_revision"
    ).filter(
        live_revision__transxchange_version__contains=TXC_21,
        live_revision__status=FeedStatus.live.value,
        live_revision__is_published=True,
    )
    count = published_datasets.count()
    logger.info(
        f"Organisation {organisation.id} has {count} "
        f"published txc 2.1 datasets to deactivate"
    )

    for dataset in published_datasets:
        live_revision: DatasetRevision = dataset.live_revision
        live_revision.to_inactive()
        live_revision.save()
        dataset.revisions.exclude(id=live_revision.id).filter(
            is_published=False
        ).delete()

    if organisation.key_contact and count > 0:
        send_data_no_longer_compliant_notification(
            organisation.key_contact.email, published_datasets
        )


def error_txc21_draft_datasets(organisation: Organisation):
    draft_datasets = organisation.dataset_set.prefetch_related("revisions").filter(
        revisions__transxchange_version__contains=TXC_21,
        live_revision__isnull=True,
        revisions__is_published=False,
        revisions__status=FeedStatus.success.value,
    )
    count = draft_datasets.count()
    logger.info(
        f"Organisation {organisation.id} has {count} "
        f"draft txc 2.1 datasets to deactivate"
    )
    for dataset in draft_datasets:
        draft_revision: DatasetRevision = dataset.revisions.latest()
        draft_revision.status = FeedStatus.error.value
        draft_revision.save()
        task = draft_revision.etl_results.order_by("-id").first()
        if not task:
            # Every revision should have a task but dont break if it doesnt
            continue

        task.status = DatasetETLTaskResult.FAILURE
        task.task_name_failed = "automatic deactivate of txc 2.1"
        task.error_code = DatasetETLTaskResult.SCHEMA_ERROR
        task.additional_info = "TransXChange schema issues found."
        task.save()

        SchemaViolation.objects.create(
            revision=draft_revision,
            filename=draft_revision.upload_file.name,
            line=0,
            details=(
                "One of the TxC files is using version 2.1 which is now unsupported"
            ),
        )


@shared_task(ignore_result=True)
def task_reprocess_file_based_datasets():
    pti_start_date = settings.PTI_START_DATE.replace(tzinfo=pytz.utc)
    before_pti = Q(live_revision__created__lt=pti_start_date)
    timetables = (
        Dataset.objects.get_active(dataset_type=TimetableType)
        .add_errored_draft_flag()
        .filter(before_pti)
        .exclude(has_errored_draft=True)
        .order_by("organisation_id", "created")
    )
    logger.info(f"DatasetETL => {timetables.count()} Timetables to update.")
    for timetable in timetables[:5]:
        reprocess_live_revision(
            dataset=timetable,
            comment=PTI_COMMENT,
            pipeline_task=task_dataset_pipeline,
        )


@shared_task()
def task_log_stuck_revisions():
    revisions = DatasetRevision.objects.get_stuck_revisions().order_by("created")
    logger.info(f"There are {revisions.count()} revisions stuck in processing.")
    for revision in revisions:
        logger.info(f"Dataset {revision.dataset_id} => Revision is stuck.")
