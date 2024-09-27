import logging
import uuid
import zipfile

from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from transit_odp.common.constants import CSVFileName
from transit_odp.common.loggers import (
    DatasetPipelineLoggerContext,
    MonitoringLoggerContext,
    PipelineAdapter,
)
from transit_odp.common.utils.s3_bucket_connection import read_datasets_file_from_s3
from transit_odp.data_quality.models import SchemaViolation
from transit_odp.fares.extract import ExtractionError, NeTExDocumentsExtractor
from transit_odp.fares.models import DataCatalogueMetaData, FaresMetadata
from transit_odp.fares.netex import NeTExValidator, get_netex_schema
from transit_odp.fares.transform import NeTExDocumentsTransformer, TransformationError
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.fares_validator.views.validate import FaresXmlValidator
from transit_odp.organisation.constants import FaresType
from transit_odp.organisation.models import Dataset, DatasetMetadata, DatasetRevision
from transit_odp.organisation.updaters import update_dataset
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.transxchange import BaseSchemaViolation
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

        context = DatasetPipelineLoggerContext(
            component_name="FaresPipeline", object_id=revision.dataset.id
        )
        adapter = PipelineAdapter(logger, {"context": context})

        task_download_fares_file(task.id, adapter)
        task_run_antivirus_check(task.id, adapter)
        task_run_fares_validation(task.id, adapter)
        task_set_fares_validation_result(task.id, adapter)
        task_run_fares_etl(task.id, adapter)

        task.update_progress(100)
        revision.refresh_from_db()
        revision.to_success()
        revision.save()

        if do_publish:
            adapter.info(f"DatasetRevision {revision_id} => Publishing fares dataset.")
            if revision.status == "success" or revision.status == "error":
                revision.publish()


@shared_task
def task_download_fares_file(task_id: int, adapter):
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

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
        adapter.info(f"Saving fares upload file - {revision.upload_file}.")
        file_ = revision.upload_file

    if not file_:
        task.to_error("dataset_validate", task.SYSTEM_ERROR)
        message = f"DatasetRevision {revision.id} doesn't contain a file."
        adapter.error(message, exc_info=True)
        raise PipelineException(message)

    task.update_progress(20)


def task_run_antivirus_check(task_id: int, adapter):
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
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
def task_run_fares_validation(task_id, adapter):
    """Task to validate a fares file."""
    violations = []
    total_files = 0
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    file_ = revision.upload_file
    # All the exceptions in the `validate` module are derived from a generic
    # ValidationException that contains a code and message, we just grab the
    # generic exception and update the task with the exception code.
    # All the exception codes match those in DatasetETLTaskResult.
    schema = get_netex_schema()
    if zipfile.is_zipfile(file_):
        adapter.info("Validating fares zip file.")
        try:
            with ZippedValidator(file_) as validator:
                validator.validate()
        except ValidationException as exc:
            adapter.error(exc.message, exc_info=True)
            task.to_error("dataset_validate", exc.code)
            task.additional_info = exc.message
            task.save()
            raise PipelineException(exc.message) from exc
        except Exception as exc:
            task.handle_general_pipeline_exception(exc, adapter)

        adapter.info("Validating fares NeTEx file.")
        violations, total_files = validate_xml_files_in_zip(
            file_, schema=schema, dataset=revision.dataset.id
        )
        adapter.info("Completed validating fares NeTEx file.")
    else:
        total_files = 1
        adapter.info("Validating fares NeTEx file.")
        violations = NeTExValidator(file_, schema=schema).validate()
        adapter.info("Completed validating fares NeTEx file.")

    adapter.info(f"{len(violations)} schema violations found")
    if len(violations) > 0:
        schema_violations = [
            SchemaViolation.from_violation(
                revision_id=revision.id, violation=BaseSchemaViolation.from_error(v)
            )
            for v in violations
        ]

        with transaction.atomic():
            # 'Update data' flow allows validation to occur multiple times
            # lets just delete any 'old' observations.
            revision.schema_violations.all().delete()
            SchemaViolation.objects.bulk_create(schema_violations, batch_size=2000)
    else:
        revision.schema_violations.all().delete()
    if len(violations) == total_files:
        adapter.error(f"Validation failed for {file_.name}", exc_info=True)
        task.to_error("dataset_validate", DatasetETLTaskResult.SCHEMA_ERROR)
        task.additional_info = f"Validation failed for {file_.name}"
        task.save()
        raise PipelineException(f"Validation failed for {file_.name}")

    task.update_progress(40)
    revision.upload_file = file_
    revision.save()


@shared_task
def task_set_fares_validation_result(task_id, adapter):
    """Task to set validation errors in a fares file/s."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision

    file_ = revision.upload_file

    org_id_list = Dataset.objects.filter(id=revision.dataset_id).values_list(
        "organisation_id", flat=True
    )

    adapter.info("Fares validation on fares file/s started.")
    fares_validator_obj = FaresXmlValidator(file_, org_id_list[0], revision.id)
    adapter.info("Setting validation errors.")
    fares_validator_obj.set_errors()
    adapter.info("Fares validation on fares file/s completed.")

    task.update_progress(50)


@shared_task
def task_run_fares_etl(task_id, adapter):
    """Task for extracting metadata from NeTEx file/s."""
    task = get_etl_task_or_pipeline_exception(task_id)
    revision = task.revision
    extracted_data = []

    task.update_progress(60)
    try:
        adapter.info("Creating fares extractor.")
        extractor = NeTExDocumentsExtractor(revision)
        extracted_data = extractor.extract()
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

    adapter.info("Loading fares metadata.")
    naptan_stop_ids = transformed_data.pop("naptan_stop_ids")
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

    adapter.info("Creating fares data catalogue metadata.")
    fares_metadata = FaresMetadata.objects.create(**transformed_data)
    for element in fares_data_catlogue:
        element.update({"fares_metadata_id": fares_metadata.id})
        # For 'Update data' flow
        DataCatalogueMetaData.objects.filter(**element).delete()
        DataCatalogueMetaData.objects.create(**element)
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


@shared_task(ignore_errors=True)
def task_update_fares_validation_existing_dataset():
    existing_fares = (
        Dataset.objects.get_existing_fares_dataset_with_no_validation_report()
    )
    count = existing_fares.count()
    logger.info(f"There are {count} datasets with no validation report.")
    for fares_dataset in existing_fares:
        logger.info(f"Running fares ETL pipeline for dataset id {fares_dataset.id}")
        revision = fares_dataset.live_revision
        revision_id = revision.id
        try:
            revision = DatasetRevision.objects.get(
                pk=revision_id, dataset__dataset_type=FaresType
            )
        except DatasetRevision.DoesNotExist as exc:
            message = f"DatasetRevision {revision_id} does not exist."
            logger.exception(message, exc_info=True)
            raise PipelineException(message) from exc

        task_id = uuid.uuid4()
        task = DatasetETLTaskResult.objects.create(
            revision=revision, status=DatasetETLTaskResult.STARTED, task_id=task_id
        )
        context = DatasetPipelineLoggerContext(
            component_name="UpdateFaresValidationExistingDataset",
            object_id=revision.dataset.id,
        )
        adapter = PipelineAdapter(logger, {"context": context})
        task_download_fares_file(task.id, adapter)
        task_set_fares_validation_result(task.id, adapter)
        task_run_fares_etl(task.id, adapter)

        task.update_progress(100)
        task.to_success()


@shared_task(ignore_errors=True)
def task_update_fares_catalogue_data_existing_datasets():
    """This is a one-off task to update the DataCatalogueMetaData model data"""
    existing_fares = Dataset.objects.get_existing_fares_dataset()
    total_count = existing_fares.count()
    logger.info(f"There are {total_count} datasets in total.")
    current_count = 0
    failed_datasets = []
    for fares_dataset in existing_fares:
        try:
            logger.info(f"Running fares ETL pipeline for dataset id {fares_dataset.id}")
            revision = fares_dataset.live_revision
            revision_id = revision.id
            try:
                revision = DatasetRevision.objects.get(
                    pk=revision_id, dataset__dataset_type=FaresType
                )
            except DatasetRevision.DoesNotExist as exc:
                message = f"DatasetRevision {revision_id} does not exist."
                logger.exception(message, exc_info=True)
                raise PipelineException(message) from exc

            context = DatasetPipelineLoggerContext(
                component_name="UpdateFaresCatalogueDataExistingDatasets",
                object_id=revision.dataset.id,
            )
            adapter = PipelineAdapter(logger, {"context": context})

            task_id = uuid.uuid4()
            task = DatasetETLTaskResult.objects.create(
                revision=revision, status=DatasetETLTaskResult.STARTED, task_id=task_id
            )

            task_download_fares_file(task.id, adapter)
            task_run_fares_etl(task.id, adapter)

            current_count += 1
            task.to_success()
            adapter.info(f"The task completed for {current_count} of {total_count}")
        except Exception as exc:
            failed_datasets.append(fares_dataset.id)
            message = f"Error processing dataset id {fares_dataset.id}: {exc}"
            adapter.exception(message, exc_info=True)
    success_count = total_count - len(failed_datasets)
    adapter.info(
        f"Total number of datasets processed successfully is {success_count} out of {total_count}"
    )
    adapter.info(
        f"The task failed to update {len(failed_datasets)} datasets with following ids: {failed_datasets}"
    )


@shared_task(ignore_errors=True)
def task_rerun_fares_validation_specific_datasets():
    """This is a one-off task to rerun the fares validator for a list of datasets
    provided in a csv file available in AWS S3 bucket
    """
    csv_file_name = CSVFileName.RERUN_FARES_VALIDATION.value
    _ids, _id_type, _ = read_datasets_file_from_s3(csv_file_name)
    logger.info(
        f"RerunFaresValidationSpecificDatasets {revision_id} => Starting fares ETL pipeline."
    )
    if not _ids and not _id_type == "dataset_ids":
        logger.info("No valid dataset IDs found in the file.")
        return
    logger.info(f"Total number of datasets to be processed: {len(_ids)}")
    fares_datasets = Dataset.objects.filter(id__in=_ids).get_active()

    if not fares_datasets:
        logger.info("No active datasets found in BODS with these dataset IDs")
        return

    processed_count = 0
    successfully_processed_ids = []
    failed_datasets = []

    total_count = fares_datasets.count()
    for fares_dataset in fares_datasets:
        logger.info(f"Running fares ETL pipeline for dataset id {fares_dataset.id}")
        revision = fares_dataset.live_revision
        if revision:
            revision_id = revision.id
            try:
                revision = DatasetRevision.objects.get(
                    pk=revision_id, dataset__dataset_type=FaresType
                )
            except DatasetRevision.DoesNotExist as exc:
                message = f"DatasetRevision {revision_id} does not exist."
                failed_datasets.append(fares_dataset.id)
                logger.exception(message, exc_info=True)
                raise PipelineException(message) from exc

            context = DatasetPipelineLoggerContext(
                component_name="RerunFaresCatalogueDataExistingDatasets",
                object_id=revision.dataset.id,
            )
            adapter = PipelineAdapter(logger, {"context": context})

            task_id = uuid.uuid4()
            task = DatasetETLTaskResult.objects.create(
                revision=revision, status=DatasetETLTaskResult.STARTED, task_id=task_id
            )

            task_download_fares_file(task.id, adapter)
            task_set_fares_validation_result(task.id, adapter)
            task_run_fares_etl(task.id, adapter)

            task.update_progress(100)
            task.to_success()
            successfully_processed_ids.append(fares_dataset.id)
            processed_count += 1
            adapter.info(f"The task completed for {processed_count} of {total_count}")

    logger.info(
        f"Total number of datasets processed successfully is {len(successfully_processed_ids)} out of {total_count}"
    )
    logger.info(
        f"The task failed to update {len(failed_datasets)} datasets with following ids: {failed_datasets}"
    )
