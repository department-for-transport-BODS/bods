import logging

import celery
from celery.app import shared_task
from django.db import transaction

from transit_odp.common.loggers import (
    DatasetPipelineLoggerContext,
    PipelineAdapter,
    get_dataset_adapter_from_revision,
)
from transit_odp.data_quality.constants import WEIGHTED_OBSERVATIONS
from transit_odp.data_quality.dataclasses import Report
from transit_odp.data_quality.dqs.client import STATUS_FAILURE, STATUS_SUCCESS
from transit_odp.data_quality.etl import TransXChangeDQPipeline
from transit_odp.data_quality.etl.model import DQModelPipeline
from transit_odp.data_quality.models import DataQualityReport
from transit_odp.data_quality.scoring import DataQualityCalculator
from transit_odp.data_quality.utils import (
    create_dqs_report,
    get_data_quality_task_or_pipeline_error,
    get_dqs_task_status,
    upload_file_to_dqs,
)
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.notifications import get_notifications
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DataQualityTask
from transit_odp.pipelines.pipelines.dqs_report_etl import (
    extract,
    transform_model,
    transform_warnings,
)
from transit_odp.timetables.loggers import DQSTaskLogger

logger = logging.getLogger(__name__)
client = get_notifications()


def get_dataset_adapter_from_report(report: DataQualityReport) -> PipelineAdapter:
    context = DatasetPipelineLoggerContext(object_id=report.revision.dataset_id)
    adapter = PipelineAdapter(logger, {"context": context})
    return adapter


def run_dqs_report_etl_pipeline(report_id: int):
    dq_report = DataQualityReport.objects.select_related("revision").get(id=report_id)
    task = DataQualityTask.objects.get(report_id=dq_report.id)
    report = Report(dq_report.file)
    adapter = get_dataset_adapter_from_report(dq_report)
    adapter.info("Running DQS report pipeline.")
    try:
        with transaction.atomic():
            adapter.info("Loading DQS model into BODS.")
            model_loader = DQModelPipeline(report_id, report.model)
            model_loader.load()

            adapter.info("Extracting data.")
            extracted = extract.run(report_id)

            adapter.info("Transforming and loading data.")
            model = transform_model.run(extracted)

            adapter.info("Transforming and loading warnings.")
            transform_warnings.run(extracted.report, model, extracted.warnings)

            pipeline = TransXChangeDQPipeline(dq_report)
            pipeline.run()

            adapter.info("Calculating Data Quality Score.")
            calculator = DataQualityCalculator(WEIGHTED_OBSERVATIONS)
            score = calculator.calculate(report_id=dq_report.id)
            dq_report.score = score
            dq_report.save()

    except Exception as exc:
        message = str(exc)
        adapter.error(message)
        task.failure(message=message)
        task.save()
        raise PipelineException(message) from exc

    adapter.info("Finished processing Data Quality Report.")


@shared_task()
def task_dqs_download(pk: int):
    """A task that downloads a DQS json report when available."""
    context = DQSTaskLogger(object_id=pk)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Downloading DQ Service report.")
    report = download_dqs_report(pk)
    return report.id


@shared_task(ignore_result=True)
def task_dqs_report_etl(report_id: int):
    """A task that runs the DQS report ETL pipeline."""
    run_dqs_report_etl_pipeline(report_id)


@shared_task(ignore_result=True)
def task_process_data_quality_report(task_id: int):
    context = DQSTaskLogger(object_id=task_id)
    adapter = PipelineAdapter(logger, {"context": context})

    adapter.info("Running DQ Service ETL jobs.")
    jobs = celery.chain(task_dqs_download.s(task_id), task_dqs_report_etl.s())
    transaction.on_commit(lambda: jobs())


def run_dqs_monitoring():
    tasks = DataQualityTask.objects.get_unfinished()
    if (count := len(tasks)) > 0:
        logger.info(f"[DQS] => Getting status for {count} tasks.")
    else:
        logger.debug(f"[DQS] => Getting status for {count} tasks.")

    for task in tasks:
        adapter = get_dataset_adapter_from_revision(logger, revision=task.revision)
        result = get_dqs_task_status(task.task_id)
        adapter.info(f"DQ Service status - {result.job_exitcode}.")

        if result.job_exitcode == STATUS_SUCCESS:
            adapter.info("DQ Service report successfully generated.")
            with transaction.atomic():
                task.success(message=result.job_status)
                task.save()
            adapter.info("Sending report to DQ ETL pipeline.")
            task_process_data_quality_report.delay(task_id=task.id)
        elif result.job_exitcode == STATUS_FAILURE:
            adapter.info(f"DQ Service job failed - {result.job_status}.")
            with transaction.atomic():
                task.failure(message=result.job_status)
                task.save()
        else:
            adapter.info("Pending response from the DQ Service.")
            with transaction.atomic():
                task.started(message=result.job_status)
                task.save()


def upload_dataset_to_dqs(task_pk):
    etl_task = get_etl_task_or_pipeline_exception(task_pk)
    revision = etl_task.revision
    dq_task = DataQualityTask.objects.get_or_create(revision=revision)
    dq_task = dq_task[0]
    adapter = get_dataset_adapter_from_revision(logger, revision)
    try:
        report_uuid = upload_file_to_dqs(revision.upload_file)
    except Exception:
        adapter.error("Unknown error occurred during DQS upload.")
        etl_task.to_error("dqs_upload", etl_task.SYSTEM_ERROR)
        dq_task.status = DataQualityTask.FAILURE
        dq_task.save()
        raise PipelineException("Unknown error with DQS.")

    if report_uuid is None:
        adapter.error("DQS did not acknowledge task.")
        raise PipelineException("DQS did not acknowledge task")

    adapter.info(f"Data set uploaded successfully to DQ Service ref: {report_uuid}.")
    dq_task.status = DataQualityTask.RECEIVED
    dq_task.task_id = report_uuid
    dq_task.save()

    return dq_task


def update_dqs_task_status(task_pk):
    etl_task = get_etl_task_or_pipeline_exception(task_pk)
    revision = etl_task.revision
    adapter = get_dataset_adapter_from_revision(logger, revision)
    try:
        dq_task = DataQualityTask.objects.get(revision=revision, status="RECEIVED")
        dq_task.status = DataQualityTask.READY
        dq_task.save()
        adapter.info(
            f"DQS task status set to READY successfully for revision {revision}."
        )
    except DataQualityTask.DoesNotExist:
        adapter.info(f"DataQualityTask with revision {revision} does not exist.")
        dq_task = None
    return dq_task


@transaction.atomic()
def download_dqs_report(pk):
    """A pipeline to download a DQS report once it is ready"""
    task = get_data_quality_task_or_pipeline_error(pk)
    adapter = get_dataset_adapter_from_revision(logger, task.revision)

    adapter.info("Downloading DQS report json file.")
    file_ = create_dqs_report(task.task_id)
    filename = f"dqs_report_{task.task_id}.json"
    report = DataQualityReport(revision=task.revision)
    report.file.save(filename, file_)
    adapter.info("DataQualityReport successfully created.")

    task.report = report
    task.save()
    adapter.info("Report added to task.")
    return report
