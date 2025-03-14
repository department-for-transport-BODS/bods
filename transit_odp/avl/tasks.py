import io
import logging
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from requests import RequestException
from urllib3.exceptions import ReadTimeoutError
from waffle import flag_is_active

from transit_odp.avl.archivers import GTFSRTArchiver
from transit_odp.avl.client import CAVLService
from transit_odp.avl.constants import (
    AWAITING_REVIEW,
    COMPLIANT,
    LOWER_THRESHOLD,
    MORE_DATA_NEEDED,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
    UNDERGOING,
)
from transit_odp.avl.enums import AVLFeedStatus
from transit_odp.avl.models import (
    AVLValidationReport,
    CAVLDataArchive,
    CAVLValidationTaskResult,
)
from transit_odp.avl.notifications import (
    send_avl_compliance_status_changed,
    send_avl_flagged_with_compliance_issue,
    send_avl_flagged_with_major_issue,
)
from transit_odp.avl.post_publishing_checks.daily.checker import PostPublishingChecker
from transit_odp.avl.post_publishing_checks.weekly import WeeklyReport
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    reset_vehicle_activity_in_cache,
)
from transit_odp.avl.validation import get_validation_client
from transit_odp.common.loggers import PipelineAdapter, get_datafeed_adapter
from transit_odp.organisation.constants import AVLType, FeedStatus
from transit_odp.organisation.models import (
    AVLComplianceCache,
    Dataset,
    DatasetMetadata,
    DatasetRevision,
)

logger = logging.getLogger(__name__)

SIRI_ZIP = "sirivm_{}.zip"
SIRI_TFL_ZIP = "sirivm_tfl_{}.zip"
VALIDATION_SAMPLE_SIZE = 250
CONFIG_API_WAIT_TIME = 25
PPC_MAX_VEHICLE_ACTIVITIES_ANALYSED = 1000


@dataclass
class ValidateResponse:
    status: str
    url: str
    created: datetime
    version: str
    username: Optional[str] = None
    password: Optional[str] = None


@shared_task()
def task_validate_avl_feed(task_id: str):
    """Task for validating an AVL feed."""
    try:
        task = CAVLValidationTaskResult.objects.get(task_id=task_id)
    except CAVLValidationTaskResult.DoesNotExist:
        logger.warning(f"CAVLValidationTaskResult {task_id} does not exist")
        return

    revision = task.revision
    cavl_service = CAVLService()
    try:
        response = cavl_service.validate_feed(
            url=revision.url_link,
            username=revision.username,
            password=revision.password,
        )
    except ReadTimeoutError:
        logger.warning("Request to Validation Service timed out.", exc_info=True)
        task.to_timeout_error()
    except Exception:
        logger.warning("Exception occurred with CAVL service", exc_info=True)
        task.to_system_error()
    else:
        if not response:
            logger.warning("CAVL service returned empty", exc_info=True)
            task.to_system_error()
        else:
            if response.status == CAVLValidationTaskResult.VALID:
                metadata, _ = DatasetMetadata.objects.update_or_create(
                    revision=revision, defaults={"schema_version": response.version}
                )
                task.to_valid()
            elif response.status == CAVLValidationTaskResult.INVALID:
                task.to_invalid()
            elif response.status == CAVLValidationTaskResult.SYSTEM_ERROR:
                task.to_system_error()
            elif response.status == CAVLValidationTaskResult.TIMEOUT_ERROR:
                task.to_timeout_error()
    task.save()


@shared_task(bind=True)
def task_create_sirivm_zipfile(self):
    URL = f"{settings.AVL_CONSUMER_API_BASE_URL}/siri-vm"
    now = timezone.now().strftime("%Y-%m-%d_%H%M%S")
    start = time.time()
    try:
        response = requests.get(URL)
        logger.info(
            f"Request to {URL} took {response.elapsed.total_seconds()} seconds for job-task_create_sirivm_zipfile"
        )
    except RequestException:
        logger.error("Unable to retrieve siri vm data.", exc_info=True)
    else:
        start_file_op = time.time()
        bytesio = io.BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr("siri.xml", response.content)

        file_ = File(bytesio, name=SIRI_ZIP.format(now))

        archive = CAVLDataArchive.objects.filter(
            data_format=CAVLDataArchive.SIRIVM
        ).last()

        if archive is None:
            archive = CAVLDataArchive(data_format=CAVLDataArchive.SIRIVM)
        end_database_op = time.time()
        logger.info(
            f"Database operation took {end_database_op-start_file_op:.2f} seconds for job-task_create_sirivm_zipfile"
        )
        archive.data = file_
        archive.save()
        end = time.time()
        logger.info(
            f"S3 archive operation took {end-end_database_op:.2f} seconds for job-task_create_sirivm_zipfile"
        )
        logger.info(
            f"Total execution took {end-start:.2f} seconds for job-task_create_sirivm_zipfile"
        )


@shared_task()
def task_create_gtfsrt_zipfile():
    is_new_gtfs_api_active = flag_is_active("", "is_new_gtfs_api_active")
    url = (
        f"{settings.GTFS_API_BASE_URL}/gtfs-rt"
        if is_new_gtfs_api_active
        else f"{settings.CAVL_CONSUMER_URL}/gtfsrtfeed"
    )
    _prefix = f"[GTFSRTArchiving] URL {url} => "
    logger.info(_prefix + "Begin archiving GTFSRT data.")
    start = time.time()
    archiver = GTFSRTArchiver(url)
    archiver.archive()
    end = time.time()
    logger.info(_prefix + f"Finished archiving in {end-start:.2f} seconds.")


@shared_task(bind=True)
def task_create_sirivm_tfl_zipfile(self):
    start = time.time()
    logger.info(f"Starting to create sirivm_tfl_zipfile with url")
    url = f"{settings.AVL_CONSUMER_API_BASE_URL}/siri-vm?downloadTfl=true"
    params = {"operatorRef": "TFLO"}
    now = timezone.now().strftime("%Y-%m-%d_%H%M%S")
    try:
        response = requests.get(url, params=params, timeout=30)
        logger.info(
            f"Request to cavl took {response.elapsed.total_seconds()} seconds for job-task_create_sirivm_tfl_zipfile"
        )
    except RequestException:
        logger.error("Unable to retrieve siri vm data for TfL.", exc_info=True)
    else:
        start_file_creation = time.time()
        bytesio = io.BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr("siri_tfl.xml", response.content)

        file_ = File(bytesio, name=SIRI_TFL_ZIP.format(now))

        archive = CAVLDataArchive.objects.filter(
            data_format=CAVLDataArchive.SIRIVM_TFL
        ).last()

        if archive is None:
            archive = CAVLDataArchive(data_format=CAVLDataArchive.SIRIVM_TFL)
        end_database_op = time.time()
        logger.info(
            f"Database operation completed in {end_database_op-start_file_creation:.2f} seconds for job-task_create_sirivm_tfl_zipfile"
        )
        archive.data = file_
        archive.save()
        end = time.time()
        logger.info(
            f"AWS bucket operation took {end-end_database_op:.2f} seconds for job-task_create_sirivm_tfl_zipfile"
        )
        logger.info(
            f"Total time elapsed to finish job-task_create_sirivm_tfl_zipfile {end-start:.2f} seconds"
        )


@shared_task(ignore_result=True)
def task_monitor_avl_feeds():
    cavl_service = CAVLService()
    feeds = cavl_service.get_feeds()

    if not feeds:
        logger.warning("No AVL data feeds to monitor")
        return

    feed_status_map = {feed.id: feed.status for feed in feeds}
    exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
    datasets = (
        Dataset.objects.select_related("live_revision", "contact")
        .filter(live_revision__isnull=False, dataset_type=AVLType)
        .exclude(live_revision__status__in=exclude_status)
    )
    revision_status_map = {
        AVLFeedStatus.live.value: FeedStatus.live.value,
        AVLFeedStatus.inactive.value: FeedStatus.inactive.value,
        AVLFeedStatus.error.value: FeedStatus.error.value,
    }

    datasets.update(avl_feed_last_checked=timezone.now())
    update_list = []
    for dataset in datasets:
        avl_feed_status = feed_status_map.get(str(dataset.id))

        if avl_feed_status is None:
            continue
        if dataset.avl_feed_status != avl_feed_status:
            new_status = feed_status_map[str(dataset.id)]
            dataset.avl_feed_status = new_status
            dataset.live_revision.status = revision_status_map.get(
                new_status, FeedStatus.error.value
            )
            update_list.append(dataset)

    logger.info(f"{len(update_list)} - AVL data feeds to update")
    Dataset.objects.bulk_update(update_list, ["avl_feed_status"])
    DatasetRevision.objects.bulk_update(
        [dataset.live_revision for dataset in update_list], ["status"]
    )


@shared_task()
def task_run_avl_validations():
    feeds = AVLDataset.objects.get_datafeeds_to_validate()
    logger.info(f"AVL Validation - {feeds.count()} feeds to validate")
    for feed in feeds:
        task_run_feed_validation(feed.id)


@shared_task()
def task_run_feed_validation(feed_id: int):
    adapter = get_datafeed_adapter(logger, feed_id)
    perform_feed_validation(adapter, feed_id)
    cache_avl_compliance_status(adapter, feed_id)


@shared_task()
def task_cache_avl_compliance_status():
    feeds = AVLDataset.objects.get_datafeeds_to_validate()
    logger.info(f"Cache AVL compliance status for {feeds.count()} feeds")
    for feed in feeds:
        adapter = get_datafeed_adapter(logger, feed.id)
        cache_avl_compliance_status(adapter, feed.id)


def perform_feed_validation(adapter: PipelineAdapter, feed_id: int):
    client = get_validation_client()

    adapter.info("Validating feed against SIRI-VM profile.")
    feeds = AVLDataset.objects.filter(id=feed_id).add_old_avl_compliance_status()
    feed = feeds.get(id=feed_id)
    old_status = feed.old_avl_compliance

    response = client.validate(feed_id=feed_id)
    if response is None:
        adapter.error(
            "An error occurred when calling the I-AVL service to validate the datafeed."
        )
        return

    adapter.info("Creating AVLValidationReport.")
    report = AVLValidationReport.from_validation_response(
        revision_id=feed.live_revision_id, response=response
    )
    report.save()

    feeds = feeds.add_avl_compliance_status()
    feed = feeds.get(id=feed_id)
    new_status = feed.avl_compliance

    if feed.post_seven_days:
        was_compliant = old_status in [UNDERGOING, AWAITING_REVIEW, COMPLIANT]
        no_longer_compliant = new_status in [
            NON_COMPLIANT,
            PARTIALLY_COMPLIANT,
            MORE_DATA_NEEDED,
        ]

        if new_status != old_status:
            if old_status == UNDERGOING and new_status == COMPLIANT:
                adapter.info(
                    f"SIRI-VM Compliance status change from {UNDERGOING} to {COMPLIANT} email has been turned off."
                )
            if old_status == UNDERGOING and new_status == MORE_DATA_NEEDED:
                adapter.info(
                    f"SIRI-VM Compliance status change from {UNDERGOING} to {MORE_DATA_NEEDED} email has been turned off."
                )
            if old_status == MORE_DATA_NEEDED and new_status == COMPLIANT:
                adapter.info(
                    f"SIRI-VM Compliance status change from {MORE_DATA_NEEDED} to {COMPLIANT} email has been turned off."
                )
            else:
                adapter.info("Status has changed send status changed email.")
                send_avl_compliance_status_changed(datafeed=feed, old_status=old_status)

        if was_compliant and report.critical_score < LOWER_THRESHOLD:
            adapter.info(f"Critical score below lower threshold of {LOWER_THRESHOLD}.")
            adapter.info("Sending major issue email.")
            send_avl_flagged_with_major_issue(dataset=feed)
        elif was_compliant and no_longer_compliant:
            if new_status == MORE_DATA_NEEDED:
                adapter.info(
                    f"SIRI-VM validation status of {MORE_DATA_NEEDED} email has been turned off."
                )
            else:
                adapter.info(f"Feed has a compliance status of {new_status}.")
                adapter.info("Sending compliance issue email.")
                send_avl_flagged_with_compliance_issue(dataset=feed, status=new_status)


def cache_avl_compliance_status(adapter: PipelineAdapter, feed_id: int):
    adapter.info(
        f"Recalculating and caching AVL feed compliance status for feed id {feed_id}"
    )
    avl_dataset = (
        AVLDataset.objects.filter(id=feed_id).add_avl_compliance_status().first()
    )
    avl_compliance = AVLComplianceCache.objects.get_or_create(dataset_id=feed_id)[0]
    avl_compliance.status = avl_dataset.avl_compliance
    avl_compliance.save()


@shared_task()
def task_daily_post_publishing_checks_single_feed(
    feed_id: int,
    report_date: date = None,
    num_activities: int = PPC_MAX_VEHICLE_ACTIVITIES_ANALYSED,
):
    """Daily task to perform Post Publishing Checks for a given feed.
    Specify a date to record in the report (even if the task runs past midnight
    before it completes).
    Specify maximum number of individual VehicleActivity instances analysed
    for this feed.
    """
    if report_date is None:
        report_date = date.today()
    logger.info(f"Perform daily post publishing checks for AVL feed ID {feed_id}")
    checker = PostPublishingChecker()
    checker.perform_checks(report_date, feed_id, num_activities)


@shared_task()
def task_daily_post_publishing_checks_all_feeds():
    avl_datasets = AVLDataset.objects.get_active_org().get_active()
    today = date.today()
    logger.info("Perform daily post publishing checks for all active AVL feeds")
    for dataset in avl_datasets:
        task_daily_post_publishing_checks_single_feed(
            feed_id=dataset.id, report_date=today
        )


@shared_task()
def task_weekly_assimilate_post_publishing_check_reports(
    start_date: str = None,
):
    start_date = date.today() if not start_date else date.fromisoformat(start_date)

    report = WeeklyReport(start_date)
    report.generate()

    is_avl_require_attention_active = flag_is_active(
        "", "is_avl_require_attention_active"
    )
    if is_avl_require_attention_active:
        logger.info("Reseting the cache for weekly PPC")
        reset_vehicle_activity_in_cache()
        logger.info("Cache reset successfully")


@shared_task()
def task_reset_avl_weekly_cache():
    logger.info("Reseting the cache for weekly PPC")
    reset_vehicle_activity_in_cache()
    logger.info("Cache reset successfully")
