import io
import json
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
from django.utils import timezone
from requests import RequestException
from urllib3.exceptions import ReadTimeoutError

from transit_odp.avl.archivers import GTFSRTArchiver
from transit_odp.avl.models import CAVLDataArchive, CAVLValidationTaskResult
from transit_odp.bods.interfaces.plugins import get_cavl_service
from transit_odp.organisation.models import DatasetMetadata

log = logging.getLogger(__name__)

SIRI_ZIP = "sirivm_{}.zip"


@dataclass
class ValidateResponse:
    status: str
    url: str
    created: datetime
    version: str
    username: Optional[str] = None
    password: Optional[str] = None


def cavl_validate_revision(revision):
    """Calls the CAVL Validate Feed service."""
    cavl_service = get_cavl_service()
    response = cavl_service.validate_feed(
        url=revision.url_link,
        username=revision.username,
        password=revision.password,
        _request_timeout=60,
        _preload_content=False,
    )
    data = json.loads(response.data)
    return ValidateResponse(**data)


@shared_task()
def task_validate_avl_feed(task_id: str):
    """ Task for validating an AVL feed."""
    try:
        task = CAVLValidationTaskResult.objects.get(task_id=task_id)
    except CAVLValidationTaskResult.DoesNotExist:
        log.warning(f"CAVLValidationTaskResult {task_id} does not exist")
        return

    revision = task.revision
    try:
        response = cavl_validate_revision(revision)
    except ReadTimeoutError:
        log.warning("Request to Validation Service timed out.", exc_info=True)
        task.to_timeout_error()
    except Exception:
        log.warning("Exception occurred with CAVL service", exc_info=True)
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
        log.error("Unable to retrieve siri vm data.", exc_info=True)
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
    log.debug(_prefix + "Begin archiving GTFSRT data.")
    start = time.time()
    archiver = GTFSRTArchiver(url)
    archiver.archive()
    end = time.time()
    log.debug(_prefix + f"Finished archivng in {end-start:.2f} seconds.")
