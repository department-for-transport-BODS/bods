import logging

from transit_odp.pipelines.exceptions import PipelineException
from transit_odp.pipelines.models import DatasetETLTaskResult


logger = logging.getLogger(__name__)


def get_etl_task_or_pipeline_exception(pk) -> DatasetETLTaskResult:
    try:
        task = DatasetETLTaskResult.objects.get(pk=pk)
    except DatasetETLTaskResult.DoesNotExist as exc:
        message = f"DatasetETLTaskResult {pk} does not exist."
        logger.exception(message, exc_info=True)
        raise PipelineException(message) from exc
    else:
        return task
