import logging

from django.db import transaction

from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.data_quality.dqs.client import STATUS_FAILURE, STATUS_SUCCESS
from transit_odp.data_quality.etl import TransXChangeDQPipeline
from transit_odp.data_quality.models import DataQualityReport
from transit_odp.data_quality.utils import (
    create_dqs_report,
    get_data_quality_task_or_pipeline_error,
    get_dqs_task_status,
    upload_file_to_dqs,
)
from transit_odp.fares.utils import get_etl_task_or_pipeline_exception
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DataQualityTask
from transit_odp.pipelines.pipelines.dqs_report_etl import (
    extract,
    transform_model,
    transform_warnings,
)

logger = logging.getLogger(__name__)
client = get_notifications()


@transaction.atomic()
def run_dqs_report_etl_pipeline(report_id: int):
    _prefix = f"[DQS] Report {report_id} => "
    logger.info(_prefix + "Running DQS report pipeline.")
    logger.info(_prefix + "Extracting data.")
    extracted = extract.run(report_id)
    logger.info(_prefix + "Successfully extracted data.")
    logger.info(_prefix + "Transforming and loading data.")
    model = transform_model.run(extracted)
    logger.info(_prefix + "Successfully transformed and loaded model.")
    logger.info(_prefix + "Transforming and loading warnings.")
    transform_warnings.run(extracted.report, model, extracted.warnings)

    # Start of new DQ Pipeline, starting with Observations extracted
    # from the transxchange file, nocs, schema versions, etc
    report: DataQualityReport = DataQualityReport.objects.select_related(
        "revision", "revision__dataset__contact", "revision__dataset__organisation"
    ).get(id=report_id)
    logger.info(_prefix + "Running BODS TxC warnings.")
    pipeline = TransXChangeDQPipeline(report)
    pipeline.run()
    contact = report.revision.dataset.contact
    if contact.is_agent_user:
        client.send_agent_reports_are_available_notification(
            dataset_id=report.revision.dataset_id,
            dataset_name=report.revision.name,
            operator_name=report.revision.dataset.organisation.name,
            short_description=report.revision.short_description,
            comments=report.revision.comment,
            draft_link=report.revision.draft_url,
            contact_email=contact.email,
        )
    else:
        client.send_reports_are_available_notification(
            dataset_id=report.revision.dataset_id,
            dataset_name=report.revision.name,
            short_description=report.revision.short_description,
            comments=report.revision.comment,
            draft_link=report.revision.draft_url,
            contact_email=contact.email,
        )
    logger.info(_prefix + "Finished processing Data Quality Report.")


@transaction.atomic()
def run_dqs_monitoring():
    tasks = DataQualityTask.objects.get_unfinished()
    count = len(tasks)
    if count > 0:
        logger.info(f"[Monitoring] => Getting status for {count} tasks.")
    else:
        logger.debug(f"[Monitoring] => Getting status for {count} tasks.")

    for task in tasks:
        _prefix = f"[DQS] DataQualityTask {task.id} => "

        result = get_dqs_task_status(task.task_id)
        if result.job_exitcode == STATUS_SUCCESS:
            task.success(message=result.job_status)
            logger.info(_prefix + f"Current status: {result.job_exitcode} - SUCCESS.")
        elif result.job_exitcode == STATUS_FAILURE:
            task.failure(message=result.job_status)
            logger.info(_prefix + f"Current status: {result.job_exitcode} - FAILURE.")
        else:
            task.started(message=result.job_status)
            logger.info(_prefix + f"Current status: {result.job_exitcode} - STARTED.")

    logger.debug("[Monitoring] => Finished monitoring.")


def upload_dataset_to_dqs(task_pk):
    _prefix = f"[DQS] DatasetETLTaskResult {task_pk} => "
    logger.info(_prefix + "Uploading file to DQS.")
    etl_task = get_etl_task_or_pipeline_exception(task_pk)
    revision = etl_task.revision
    dq_task = DataQualityTask.objects.create(revision=revision)

    try:
        report_uuid = upload_file_to_dqs(revision.upload_file)
    except Exception:
        logger.error(_prefix + "Unknown error occurred during DQS upload.")
        etl_task.to_error("dqs_upload", etl_task.SYSTEM_ERROR)
        dq_task.status = DataQualityTask.FAILURE
        dq_task.save()
        raise PipelineException("Unknown error with DQS.")

    if report_uuid is None:
        logger.error(_prefix + "DQS did not acknowledge task.")
        raise PipelineException("DQS did not acknowledge task")

    logger.info(_prefix + f"Upload successfully DQS ref: {report_uuid}.")
    dq_task.status = DataQualityTask.RECEIVED
    dq_task.task_id = report_uuid
    dq_task.save()

    return dq_task


@transaction.atomic()
def download_dqs_report(pk):
    """A pipeline to download a DQS report once it is ready"""
    _prefix = f"[DQS] DataQualityTask {pk} => "
    logger.info(_prefix + "Downloading DQS report json file.")

    task = get_data_quality_task_or_pipeline_error(pk)

    file_ = create_dqs_report(task.task_id)
    filename = f"dqs_report_{task.task_id}.json"
    report = DataQualityReport(revision=task.revision)
    report.file.save(filename, file_)
    logger.info(_prefix + "DataQualityReport successfully created.")

    task.report = report
    task.save()
    logger.info(_prefix + "Report added to task.")
    return report
