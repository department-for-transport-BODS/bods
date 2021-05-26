import logging

from django.core.files.base import ContentFile
from tenacity import before_log, retry, stop_after_attempt, wait_random_exponential

from transit_odp.data_quality.dqs.client import DQSClient
from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DataQualityTask

logger = logging.getLogger(__name__)


def get_data_quality_task_or_pipeline_error(pk):
    try:
        task = DataQualityTask.objects.get(id=pk)
    except DataQualityTask.DoesNotExist as exc:
        message = f"DataQualityTask {pk} does not exist."
        logger.exception(message, exc_info=True)
        raise PipelineException(message) from exc
    else:
        return task


@retry(
    reraise=True,
    wait=wait_random_exponential(multiplier=1, max=4),
    stop=stop_after_attempt(3),
    before=before_log(logger, logging.DEBUG),
)
def get_dqs_task_status(task_id):
    dqs = DQSClient()
    return dqs.get_status(task_id)


def create_dqs_report(task_id):
    dqs = DQSClient()
    data = dqs.download(task_id)
    logger.info(f"DQS report downloaded successfully for {task_id}")
    return ContentFile(data)


@retry(
    reraise=True,
    wait=wait_random_exponential(multiplier=0.5, max=10),
    stop=stop_after_attempt(5),
    before=before_log(logger, logging.DEBUG),
)
def upload_file_to_dqs(file_):
    logger.info(f"Uploading {file_.name} to DQS")
    dqs = DQSClient()
    report_uuid = dqs.upload(file_)
    return report_uuid
