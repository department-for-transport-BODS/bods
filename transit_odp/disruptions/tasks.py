import io
import logging
import time
from dataclasses import dataclass
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from requests import RequestException

from transit_odp.disruptions.models import DisruptionsDataArchive


logger = logging.getLogger(__name__)

SIRI_ZIP = "sirisx_{}.zip"


@shared_task(bind=True)
def task_create_sirisx_zipfile(self):
    URL = f"{settings.DISRUPTIONS_API_URL}"
    now = timezone.now().strftime("%Y-%m-%d_%H%M%S")
    start = time.time()
    try:
        response = requests.get(
            URL, headers={"x-api-key": settings.DISRUPTIONS_API_KEY}
        )

        logger.info(
            f"Request to {URL} took {response.elapsed.total_seconds()} seconds for job-task_create_sirisx_zipfile"
        )
    except RequestException:
        logger.error("Unable to retrieve siri sx data.", exc_info=True)
    else:
        start_file_op = time.time()
        bytesio = io.BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr("sirisx.xml", response.content)

        file_ = File(bytesio, name=SIRI_ZIP.format(now))

        archive = DisruptionsDataArchive.objects.last()

        if archive is None:
            archive = DisruptionsDataArchive()
        end_database_op = time.time()
        logger.info(
            f"Database operation took {end_database_op-start_file_op:.2f} seconds for job-task_create_sirisx_zipfile"
        )
        archive.data = file_
        archive.save()
        end = time.time()
        logger.info(
            f"S3 archive operation took {end-end_database_op:.2f} seconds for job-task_create_sirisx_zipfile"
        )
        logger.info(
            f"Total execution took {end-start:.2f} seconds for job-task_create_sirisx_zipfile"
        )
