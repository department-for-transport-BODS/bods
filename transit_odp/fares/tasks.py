import logging
import zipfile

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from waffle import flag_is_active

from transit_odp.common.loggers import (
    DatasetPipelineLoggerContext,
    MonitoringLoggerContext,
    PipelineAdapter,
)
from transit_odp.fares.extract import ExtractionError, NeTExDocumentsExtractor
from transit_odp.fares.models import DataCatalogueMetaData, FaresMetadata
from transit_odp.fares.netex import (
    NeTExValidator,
    get_documents_from_file,
    get_netex_schema,
)
from transit_odp.fares.transform import NeTExDocumentsTransformer, TransformationError
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.organisation.constants import FaresType
from transit_odp.organisation.models import Dataset, DatasetMetadata, DatasetRevision
from transit_odp.organisation.updaters import update_dataset
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.validate import (
    DataDownloader,
    DownloadException,
    FileScanner,
    ValidationException,
    ZippedValidator,
)
from transit_odp.validate.xml import validate_xml_files_in_zip

logger = logging.getLogger(__name__)

DT_FORMAT = "%Y-%m-%d_%H-%M-%S"


@shared_task(bind=True)
def task_run_fares_pipeline(self, revision_id: int, do_publish: bool = False):
    logger.info(f"DatasetRevision {revision_id} => Starting fares ETL pipeline.")
    try:
        revision = DatasetRevision.objects.get(
            pk=revision_id, dataset__dataset_type=FaresType
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

        task_download_fares_file(task.id)
        task_run_antivirus_check(task.id)
        # task_run_fares_validation(task.id)
        task_run_fares_etl(task.id)

        task.update_progress(100)
        revision.refresh_from_db()
        revision.to_success()
        revision.save()

        if do_publish:
            logger.info(f"DatasetRevision {revision_id} => Publishing fares dataset.")
            if revision.status == "success" or revision.status == "error":
                revision.publish()


@shared_task
def task_download_fares_file(task_id: int):
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    context = DatasetPipelineLoggerContext(object_id=revision.dataset.id)
    adapter = PipelineAdapter(logger, {"context": context})

    task.update_progress(10)
    if revision.url_link:
        adapter.info(f"Downloading fares file from {revision.url_link}.")
        now = timezone.now().strftime(DT_FORMAT)
        try:
            downloader = DataDownloader(revision.url_link)
            response = downloader.get()
        except DownloadException as exc:
            adapter.error(exc.message, exc_info=True)
            task.to_error("dataset_download", task.SYSTEM_ERROR)
            raise PipelineException(exc.message) from exc
        else:
            adapter.info("Fares file downloaded successfully.")
            name = f"remote_dataset_{revision.dataset.id}_{now}.{response.filetype}"
            file_ = ContentFile(response.content, name=name)
            revision.upload_file = file_
            revision.save()
    else:
        file_ = revision.upload_file

    if not file_:
        task.to_error("dataset_validate", task.SYSTEM_ERROR)
        message = f"DatasetRevision {revision.id} doesn't contain a file."
        adapter.error(message, exc_info=True)
        raise PipelineException(message)

    task.update_progress(20)


def task_run_antivirus_check(task_id: int):
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    context = DatasetPipelineLoggerContext(object_id=revision.dataset.id)
    adapter = PipelineAdapter(logger, {"context": context})
    file_ = revision.upload_file
    try:
        scanner = FileScanner(settings.CLAMAV_HOST, settings.CLAMAV_PORT)
        adapter.info("Virus scanning fares file.")
        scanner.scan(file_)
    except ValidationException as exc:
        adapter.error(exc.message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = exc.message
        task.save()
        raise PipelineException(exc.message) from exc
    except Exception as exc:
        task.handle_general_pipeline_exception(exc, adapter)

    task.update_progress(30)


@shared_task
def task_run_fares_validation(task_id):
    """Task to validate a fares file."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    context = DatasetPipelineLoggerContext(object_id=revision.dataset.id)
    adapter = PipelineAdapter(logger, {"context": context})

    file_ = revision.upload_file
    # All the exceptions in the `validate` module are derived from a generic
    # ValidationException that contains a code and message, we just grab the
    # generic exception and update the task with the exception code.
    # All the exception codes match those in DatasetETLTaskResult.
    try:
        schema = get_netex_schema()
        if zipfile.is_zipfile(file_):
            adapter.info("Validating fares zip file.")
            with ZippedValidator(file_) as validator:
                validator.validate()
            adapter.info("Validating fares NeTEx file.")
            validate_xml_files_in_zip(file_, schema=schema)
        else:
            adapter.info("Validating fares NeTEx file.")
            NeTExValidator(file_, schema=schema).validate()
    except ValidationException as exc:
        adapter.error(exc.message, exc_info=True)
        task.to_error("dataset_validate", exc.code)
        task.additional_info = exc.message
        task.save()
        raise PipelineException(exc.message) from exc
    except Exception as exc:
        task.handle_general_pipeline_exception(exc, adapter)

    task.update_progress(40)
    revision.upload_file = file_
    revision.save()


@shared_task
def task_run_fares_etl(task_id):
    """Task for extracting metadata from NeTEx file/s."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    context = DatasetPipelineLoggerContext(object_id=revision.dataset.id)
    adapter = PipelineAdapter(logger, {"context": context})

    file_ = revision.upload_file
    docs = get_documents_from_file(file_)

    task.update_progress(60)
    try:
        adapter.info("Creating fares extractor.")
        extractor = NeTExDocumentsExtractor(docs)
        extracted_data = extractor.to_dict()
    except ExtractionError as exc:
        adapter.error("Metadata extraction failed.", exc_info=True)
        task.to_error("dataset_etl", exc.code)
        raise PipelineException(exc.message) from exc
    except Exception as exc:
        task.handle_general_pipeline_exception(exc, adapter)

    task.update_progress(70)
    try:
        adapter.info("Transforming NeTEx stops")
        transform = NeTExDocumentsTransformer(extracted_data)
        transformed_data = transform.transform_data()
    except TransformationError as exc:
        adapter.error("Metadata transformation failed.", exc_info=True)
        task.to_error("dataset_etl", exc.code)
        raise PipelineException(exc.message) from exc
    except Exception as exc:
        task.handle_general_pipeline_exception(exc, adapter)

    task.update_progress(90)

    naptan_stop_ids = transformed_data.pop("naptan_stop_ids")
    is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
    if is_fares_validator_active:
        fares_data_catlogue = transformed_data.pop("fares_data_catalogue")
    # Load metadata
    # This block can be moved to a load module when we extract/load more metadata
    # like localities, admin areas
    transformed_data["revision"] = revision

    # For 'Update data' flow which allows validation to occur multiple times
    metadata_ids_list = DatasetMetadata.objects.filter(
        revision_id=revision.id
    ).values_list("id")
    FaresMetadata.objects.filter(datasetmetadata_ptr__in=metadata_ids_list).delete()
    fares_metadata = FaresMetadata.objects.create(**transformed_data)
    if is_fares_validator_active:
        for element in fares_data_catlogue:
            element.update({"fares_metadata_id": fares_metadata.id})
            # For 'Update data' flow
            DataCatalogueMetaData.objects.filter(**element).delete()
            DataCatalogueMetaData.objects.create(**element)
    # For 'Update data' flow
    fares_metadata.stops.remove(*naptan_stop_ids)
    fares_metadata.stops.add(*naptan_stop_ids)
    adapter.info("Fares metadata loaded.")


@shared_task(ignore_errors=True)
def task_update_remote_fares():
    fares = Dataset.objects.get_available_remote_fares()
    context = MonitoringLoggerContext(object_id=0)
    adapter = PipelineAdapter(logger, {"context": context})
    count = fares.count()
    adapter.info(f"{count} datasets to check.")
    for fare in fares:
        update_dataset(fare, task_run_fares_pipeline)


@shared_task(ignore_result=True)
def task_retry_unavailable_fares():
    fares = Dataset.objects.get_unavailable_remote_fares()
    context = MonitoringLoggerContext(object_id=-1)
    adapter = PipelineAdapter(logger, {"context": context})
    count = fares.count()
    adapter.info(f"{count} datasets to check.")
    for fare in fares:
        update_dataset(fare, task_run_fares_pipeline)
