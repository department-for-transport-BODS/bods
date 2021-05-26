from celery import shared_task
from celery.utils.log import get_task_logger

from transit_odp.bods import bootstrap
from transit_odp.bods.domain import commands
from transit_odp.data_quality.tasks import (
    download_dqs_report,
    run_dqs_monitoring,
    run_dqs_report_etl_pipeline,
)
from transit_odp.pipelines.pipelines.data_archive import (
    bulk_data_archive,
    change_data_archive,
)
from transit_odp.pipelines.pipelines.naptan_etl import main

logger = get_task_logger(__name__)


bus = bootstrap.bootstrap()


@shared_task(ignore_result=True)
def task_dqs_monitor():
    """A task that monitors the Data Quality Service."""
    logger.info("[Monitoring] => Starting DQS monitoring job.")
    run_dqs_monitoring()


@shared_task()
def task_dqs_download(pk: int):
    """A task that downloads a DQS json report when available."""
    logger.info(f"[DQS] DataQualityTask {pk} => Downloading DQ Service report.")
    report = download_dqs_report(pk)
    return report.id


@shared_task(ignore_result=True)
def task_dqs_report_etl(report_id: int):
    """A task that runs the DQS report ETL pipeline."""
    logger.info(f"[DQS] Report {report_id} => Starting DQS report pipeline.")
    run_dqs_report_etl_pipeline(report_id)


@shared_task(ignore_result=True)
def task_create_bulk_data_archive():
    bulk_data_archive.run()


@shared_task(ignore_result=True)
def task_create_change_data_archive():
    change_data_archive.run()


@shared_task(ignore_result=True)
def task_run_naptan_etl():
    main.run()


@shared_task(ignore_result=True)
def task_monitor_avl_feeds():
    # TODO - add e2e test for this entrypoint
    bus.handle(commands.MonitorAVLFeeds())
