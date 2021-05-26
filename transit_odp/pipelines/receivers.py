import celery
from django.db import transaction
from django.dispatch import receiver

from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.models import DatasetRevision
from transit_odp.organisation.receivers import logger
from transit_odp.pipelines.models import DataQualityTask
from transit_odp.pipelines.signals import dataset_changed, dataset_etl, dqs_report_etl
from transit_odp.pipelines.tasks import task_dqs_download, task_dqs_report_etl
from transit_odp.timetables.tasks import task_dataset_pipeline


@receiver(dataset_etl)
def dataset_etl_handler(sender, revision: DatasetRevision, **kwargs):
    """
    Listens on the feed_index and dispatches a Celery job to process the feed payload
    """
    logger.debug(f"index_feed_handler called for DatasetRevision {revision.id}")

    if not revision.status == FeedStatus.pending.value:
        revision.to_pending()
        revision.save()

    # Trigger task once transactions have been fully committed
    transaction.on_commit(lambda: task_dataset_pipeline.delay(revision.id))


@receiver(dqs_report_etl)
def dqs_report_etl_handler(sender, task: DataQualityTask, **kwargs):
    """
    Listens on the dqs_report_etl and dispatches a Celery job chain to
    process the ready DQS report
    """
    logger.debug(
        f"dqs_report_etl_handler called for "
        f"DataQualityTask(id={task.id}, task_id={task.task_id})"
    )
    # Chain Celery tasks: download the report and then run ETL pipeline
    transaction.on_commit(
        lambda: celery.chain(task_dqs_download.s(task.id), task_dqs_report_etl.s())()
    )


@receiver(dataset_changed)
def dataset_changed_handler(sender, revision: DatasetRevision, **kwargs):
    """
    Listens on the task_dataset_etl and dispatches a Celery job to publish the revision
    """
    logger.debug(f"dataset_changed called for DatasetRevision {revision.id}")
    task_dataset_pipeline.apply_async(args=(revision.id,), kwargs={"do_publish": True})
