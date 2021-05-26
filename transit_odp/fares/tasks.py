import logging
import zipfile

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from transit_odp.fares.extract import ExtractionError, NeTExDocumentsExtractor
from transit_odp.fares.models import FaresMetadata
from transit_odp.fares.netex import (
    NeTExValidator,
    get_documents_from_file,
    validate_netex_files_in_zip,
)
from transit_odp.fares.transform import NeTExDocumentsTransformer, TransformationError
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import DatasetRevision
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.validate import (
    DataDownloader,
    DownloadException,
    FileScanner,
    ValidationException,
    ZippedValidator,
)

logger = logging.getLogger(__name__)

DT_FORMAT = "%Y-%m-%d_%H-%M-%S"


@shared_task(bind=True)
def task_run_fares_pipeline(self, revision_id):
    try:
        revision = DatasetRevision.objects.get(
            pk=revision_id, dataset__dataset_type=DatasetType.FARES.value
        )
    except DatasetRevision.DoesNotExist as exc:
        message = f"DatasetRevision {revision_id} does not exist."
        logger.exception(message, exc_info=True)
        raise PipelineException(message) from exc
    else:
        revision.to_indexing()
        revision.save()
        task = DatasetETLTaskResult.objects.create(
            revision=revision,
            status=DatasetETLTaskResult.STARTED,
            task_id=self.request.id,
        )
        task.update_progress(10)
        logger.info("Task %d => validating fares file.", task.pk)
        task_run_fares_validation(task.id)
        task.update_progress(40)
        logger.info("Task %d => extracting fares metadata.", task.pk)
        task_run_fares_etl(task.id)
        logger.info("Task %d => successfully processed fares file.", task.pk)
        task.update_progress(100)
        revision.refresh_from_db()
        revision.to_success()
        revision.save()


@shared_task
def task_run_fares_validation(task_id):
    """Task to validate a fares file."""

    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    # If a user has provided a link instead of a file
    if revision.url_link:
        logger.info(
            "Task %d => downloading fares file from %s.", task_id, revision.url_link
        )
        now = timezone.now().strftime(DT_FORMAT)
        try:
            downloader = DataDownloader(revision.url_link)
            response = downloader.get()
        except DownloadException as exc:
            logger.error(exc.message, exc_info=True)
            task.to_error("dataset_download", task.SYSTEM_ERROR)
            raise PipelineException(exc.message) from exc
        else:
            logger.info(
                "Task %d => fares file downloaded successfully.",
                task_id,
            )
            name = f"remote_dataset_{revision.dataset.id}_{now}.{response.filetype}"
            file_ = ContentFile(response.content, name=name)
    else:
        file_ = revision.upload_file

    if not file_:
        task.to_error("dataset_validate", task.SYSTEM_ERROR)
        message = f"DatasetRevision {revision.id} doesn't contain a file."
        logger.error(message, exc_info=True)
        raise PipelineException(message)

    # All the exceptions in the `validate` module are derived from a generic
    # ValidationException that contains a code and message, we just grab the
    # generic exception and update the task with the exception code.
    # All the exception codes match those in DatasetETLTaskResult.
    try:
        if zipfile.is_zipfile(file_):
            logger.info("Task %d => validating fares zip file.", task.pk)
            with ZippedValidator(file_) as validator:
                validator.validate()
            logger.info("Task %d => validating fares NeTEx file.", task.pk)
            validate_netex_files_in_zip(file_)
        else:
            logger.info("Task %d => validating fares NeTEx file.", task.pk)
            NeTExValidator(file_).validate()

        task.update_progress(50)
        scanner = FileScanner(settings.CLAMAV_HOST, settings.CLAMAV_PORT)
        logger.info("Task %d => virus scanning fares file.", task.pk)
        scanner.scan(file_)
    except ValidationException as exc:
        logger.error(exc.message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = exc.message
        task.save()
        raise PipelineException(exc.message) from exc
    revision.upload_file = file_
    revision.save()


@shared_task
def task_run_fares_etl(task_id):
    """Task for extracting metadata from NeTEx file/s."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    file_ = revision.upload_file
    docs = get_documents_from_file(file_)

    try:
        logger.info("Task %d => creating fares extractor.", task.pk)
        extractor = NeTExDocumentsExtractor(docs)
        extracted_data = extractor.to_dict()
    except ExtractionError as exc:
        logger.error("Metadata extraction for task {task_id} failed.", exc_info=True)
        task.to_error("dataset_etl", exc.code)
        raise PipelineException(exc.message) from exc

    task.update_progress(70)
    try:
        logger.info("Task %d => transforming netex stops", task.pk)
        transform = NeTExDocumentsTransformer(extracted_data)
        transformed_data = transform.transform_data()
    except TransformationError as exc:
        logger.error(
            "Metadata transformation for task {task_id} failed.", exc_info=True
        )
        task.to_error("dataset_etl", exc.code)
        raise PipelineException(exc.message) from exc

    task.update_progress(90)

    naptan_stop_ids = transformed_data.pop("naptan_stop_ids")
    # Load metadata
    # This block can be moved to a load module when we extract/load more metadata
    # like localities, admin areas
    transformed_data["revision"] = revision
    fares_metadata = FaresMetadata.objects.create(**transformed_data)
    fares_metadata.stops.add(*naptan_stop_ids)
    logger.info("Task %d => fares metadata loaded.", task.pk)
