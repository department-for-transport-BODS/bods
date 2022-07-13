import io
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils import timezone
from requests import RequestException
from urllib3.exceptions import ReadTimeoutError

from transit_odp.avl.archivers import GTFSRTArchiver
from transit_odp.avl.constants import (
    AWAITING_REVIEW,
    COMPLIANT,
    LOWER_THRESHOLD,
    MORE_DATA_NEEDED,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
    UNDERGOING,
)
from transit_odp.avl.models import (
    AVLSchemaValidationReport,
    AVLValidationReport,
    CAVLDataArchive,
    CAVLValidationTaskResult,
)
from transit_odp.avl.notifications import (
    send_avl_compliance_status_changed,
    send_avl_feed_down_notification,
    send_avl_flagged_with_compliance_issue,
    send_avl_flagged_with_major_issue,
    send_avl_report_requires_resolution_notification,
    send_avl_schema_check_fail,
    send_avl_status_changed_notification,
)
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.validation import get_validation_client
from transit_odp.bods.interfaces.plugins import get_cavl_service
from transit_odp.common.loggers import get_datafeed_adapter
from transit_odp.organisation.constants import (
    AVLFeedDeploying,
    AVLFeedDown,
    AVLFeedUp,
    AVLType,
    FeedStatus,
)
from transit_odp.organisation.models import Dataset, DatasetMetadata, DatasetRevision

logger = logging.getLogger(__name__)

SIRI_ZIP = "sirivm_{}.zip"
SIRI_TFL_ZIP = "sirivm_tfl_{}.zip"
VALIDATION_SAMPLE_SIZE = 250
CONFIG_API_WAIT_TIME = 25


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
    cavl_service = get_cavl_service()
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
    URL = f"{settings.CAVL_CONSUMER_URL}/datafeed"
    now = timezone.now().strftime("%Y-%m-%d_%H%M%S")

    try:
        response = requests.get(URL)
    except RequestException:
        logger.error("Unable to retrieve siri vm data.", exc_info=True)
    else:
        bytesio = io.BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr("siri.xml", response.content)

        file_ = File(bytesio, name=SIRI_ZIP.format(now))

        archive = CAVLDataArchive.objects.filter(
            data_format=CAVLDataArchive.SIRIVM
        ).last()

        if archive is None:
            archive = CAVLDataArchive(data_format=CAVLDataArchive.SIRIVM)

        archive.data = file_
        archive.save()


@shared_task()
def task_create_gtfsrt_zipfile():
    url = f"{settings.CAVL_CONSUMER_URL}/gtfsrtfeed"
    _prefix = f"[GTFSRTArchiving] URL {url} => "
    logger.debug(_prefix + "Begin archiving GTFSRT data.")
    start = time.time()
    archiver = GTFSRTArchiver(url)
    archiver.archive()
    end = time.time()
    logger.debug(_prefix + f"Finished archivng in {end-start:.2f} seconds.")


@shared_task(bind=True)
def task_create_sirivm_tfl_zipfile(self):
    url = f"{settings.CAVL_CONSUMER_URL}/datafeed"
    params = {"operatorRef": "TFLO"}
    now = timezone.now().strftime("%Y-%m-%d_%H%M%S")

    try:
        response = requests.get(url, params=params, timeout=30)
    except RequestException:
        logger.error("Unable to retrieve siri vm data for TfL.", exc_info=True)
    else:
        bytesio = io.BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr("siri_tfl.xml", response.content)

        file_ = File(bytesio, name=SIRI_TFL_ZIP.format(now))

        archive = CAVLDataArchive.objects.filter(
            data_format=CAVLDataArchive.SIRIVM_TFL
        ).last()

        if archive is None:
            archive = CAVLDataArchive(data_format=CAVLDataArchive.SIRIVM_TFL)

        archive.data = file_
        archive.save()


@shared_task(ignore_result=True)
def task_monitor_avl_feeds():
    cavl_service = get_cavl_service()
    feed_status_map = {feed.id: feed.status.value for feed in cavl_service.get_feeds()}
    exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
    datasets = (
        Dataset.objects.select_related("live_revision", "contact")
        .filter(live_revision__isnull=False, dataset_type=AVLType)
        .exclude(live_revision__status__in=exclude_status)
    )
    revision_status_map = {
        AVLFeedUp: FeedStatus.live.value,
        AVLFeedDeploying: FeedStatus.live.value,
        AVLFeedDown: FeedStatus.error.value,
    }

    datasets.update(avl_feed_last_checked=timezone.now())
    update_list = []
    for dataset in datasets:
        avl_feed_status = feed_status_map.get(dataset.id)
        if avl_feed_status is None:
            continue
        if dataset.avl_feed_status != avl_feed_status:
            new_status = feed_status_map[dataset.id]
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

    for dataset in update_list:
        send_avl_status_changed_notification(dataset)
        if dataset.avl_feed_status == AVLFeedDown:
            send_avl_feed_down_notification(dataset)


@shared_task()
def task_run_avl_validations():
    feeds = AVLDataset.objects.get_datafeeds_to_validate()
    logger.info(f"AVL Validation - {feeds.count()} feeds to validate")
    for feed in feeds:
        task_run_feed_validation(feed.id)


@shared_task()
def task_run_feed_validation(feed_id: int):
    adapter = get_datafeed_adapter(logger, feed_id)
    client = get_validation_client()

    adapter.info("Validating feed against SIRI-VM schema.")
    response = client.schema(feed_id=feed_id)

    if len(response.errors) > 0:
        adapter.info("Feed failed SIRI-VM schema validation.")
        feed = AVLDataset.objects.get(id=feed_id)
        revision = feed.live_revision
        # Sleeping to give the config api time to be available
        time.sleep(CONFIG_API_WAIT_TIME)
        with transaction.atomic():
            cavl_service = get_cavl_service()
            deleted = cavl_service.delete_feed(feed_id=feed_id)
            if not deleted:
                adapter.error("Unable to de-register feed.")
                return

            AVLSchemaValidationReport.from_schema_validation_response(
                revision_id=feed.live_revision_id, response=response
            ).save()
            revision.to_inactive()
            revision.save()
            send_avl_schema_check_fail(feed)

        return

    adapter.info("Validating feed against BODS SIRI-VM profile.")
    feeds = AVLDataset.objects.filter(id=feed_id).add_old_avl_compliance_status()
    feed = feeds.get(id=feed_id)
    old_status = feed.old_avl_compliance

    response = client.validate(feed_id=feed_id, sample_size=VALIDATION_SAMPLE_SIZE)
    if response is None:
        adapter.error("BODS SIRI-VM profile validation failed.")
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
            adapter.info("Status has changed send status changed email.")
            send_avl_compliance_status_changed(datafeed=feed, old_status=old_status)

        if was_compliant and report.critical_score < LOWER_THRESHOLD:
            adapter.info(f"Critical score below lower threshold of {LOWER_THRESHOLD}.")
            adapter.info("Sending major issue email.")
            send_avl_flagged_with_major_issue(dataset=feed)
        elif was_compliant and no_longer_compliant:
            adapter.info(f"Feed has a compliance status of {new_status}.")
            adapter.info("Sending compliance issue email.")
            send_avl_flagged_with_compliance_issue(dataset=feed, status=new_status)
    else:
        send_email = (old_status == UNDERGOING) and (new_status == AWAITING_REVIEW)
        if send_email:
            adapter.info("Sending requires resolution email.")
            send_avl_report_requires_resolution_notification(dataset=feed)
