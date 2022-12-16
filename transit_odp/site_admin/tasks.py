import logging
from datetime import timedelta

from celery import shared_task
from dateutil.relativedelta import relativedelta
from django.core.files.base import File
from django.utils import timezone

from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.feedback.models import Feedback
from transit_odp.site_admin.constants import (
    ARCHIVE_CATEGORY_FILENAME,
    OperationalMetrics,
)
from transit_odp.site_admin.exports import (
    create_metrics_archive,
    create_operational_exports_file,
)
from transit_odp.site_admin.models import (
    APIRequest,
    DocumentArchive,
    OperationalStats,
    ResourceRequestCounter,
)
from transit_odp.site_admin.stats import (
    get_active_dataset_counts,
    get_operator_count,
    get_orgs_with_active_dataset_counts,
    get_service_code_counts,
    get_siri_vm_vehicle_counts,
    get_user_counts,
)

logger = logging.getLogger(__name__)
DATA_RETENTION_POLICY_MONTHS = 3
FEEDBACK_RETENTION_POLICY_MONTHS = 24
MIN_DAYS_WEEKLY_PPC_REPORT = 90
MIN_DAYS_DAILY_PPC_REPORT = 28


@shared_task()
def task_save_operational_stats():
    """A task to save operational stats for the current day

    date: todays date

    operator_count: number of active operators

    operator_user_count: number of active org admins + org staff in active orgs
    agent_user_count: number of active agent users
    consumer_count: number of active consumer users

    timetables_count: total number of active timetables from active orgs
    avl_count: total number of active avl feeds (regardless of status) from
        active orgs
    fares_count: total number of active fares from active orgs

    published_timetable_operator_count: number of operators with active
        timetables
    published_avl_operator_count: number of operators with active avl feeds
    published_fares_operator_count: number of operators with active fares

    vehicle_counts: The number of vehicles RT has encountered for that day

    registered_service_code_count: The number of unique registered service
        codes in published, active datasets
    unregistered_service_code_count: The number of unique unregistered service
        codes in published, active datasets
    """
    date = timezone.now().date()
    stats = {
        "operator_count": get_operator_count(),
        "vehicle_count": get_siri_vm_vehicle_counts(),
    }
    stats.update(get_user_counts())
    stats.update(get_active_dataset_counts())
    stats.update(get_orgs_with_active_dataset_counts())

    stats.update(get_service_code_counts())

    OperationalStats.objects.update_or_create(date=date, defaults=stats)


@shared_task()
def task_create_daily_api_stats():
    """
    Creates a MetricArchive for this month.
    """
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(seconds=1)
    first_of_month = yesterday.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    logger.info(
        "[MetricArchive] Creating metrics archive for "
        f"{first_of_month:%Y-%m-%d} to {yesterday:%Y-%m-%d}"
    )
    create_metrics_archive(start=first_of_month, end=yesterday)


@shared_task()
def task_backfill_metrics_archive():
    """
    Backfills all the previous months MetricArchive's.
    """
    requests = APIRequest.objects.order_by("id")
    first_created = timezone.localtime(requests.first().created)
    last_created = timezone.localtime(requests.last().created)

    start = first_created.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    while start < last_created:
        end = (start + relativedelta(months=1)) - timedelta(seconds=1)
        logger.info(
            "[MetricArchive] Backfilling metrics archive for "
            f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"
        )
        create_metrics_archive(start=start, end=end)
        start = start + relativedelta(months=1)


@shared_task()
def task_create_operational_exports_archive():
    filename = ARCHIVE_CATEGORY_FILENAME[OperationalMetrics]
    buffer_ = create_operational_exports_file()
    archive = File(buffer_, name=filename)

    logger.info("[OperationalMetricsArchive] Creating operational metrics export.")
    metrics = (
        DocumentArchive.objects.filter(category=OperationalMetrics)
        .order_by("modified")
        .last()
    )
    if metrics is None:
        DocumentArchive.objects.create(archive=archive, category=OperationalMetrics)
    else:
        metrics.archive.save(filename, archive)


@shared_task()
def task_delete_unwanted_data():
    now = timezone.now()
    api_request_cutoff = now - relativedelta(months=DATA_RETENTION_POLICY_MONTHS)

    deleted, _ = APIRequest.objects.filter(created__lt=api_request_cutoff).delete()
    logger.info(f"Deleted {deleted} API request logs")

    deleted, _ = ResourceRequestCounter.objects.filter(
        date__lt=api_request_cutoff.date()
    ).delete()
    logger.info(f"Deleted {deleted} Resource request logs")

    website_feedback_policy = relativedelta(months=FEEDBACK_RETENTION_POLICY_MONTHS)
    website_feedback_cutoff = now.date() - website_feedback_policy
    deleted, _ = Feedback.objects.filter(date__lte=website_feedback_cutoff).delete()
    logger.info(f"Deleted {deleted} website feedback instances")

    daily_ppc_reports = now.date() - timedelta(days=MIN_DAYS_DAILY_PPC_REPORT)
    deleted, _ = (
        PostPublishingCheckReport.objects.filter(granularity=PPCReportType.DAILY)
        .filter(created__lt=daily_ppc_reports)
        .delete()
    )
    logger.info(f"Deleted {deleted} post publishing check daily report")

    weekly_ppc_reports = now.date() - timedelta(days=MIN_DAYS_WEEKLY_PPC_REPORT)
    deleted, _ = (
        PostPublishingCheckReport.objects.filter(granularity=PPCReportType.WEEKLY)
        .filter(created__lt=weekly_ppc_reports)
        .delete()
    )
    logger.info(f"Deleted {deleted} post publishing check weekly report")
