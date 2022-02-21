import logging

from celery import shared_task
from django.core.files.base import File

from transit_odp.browse.exports import create_data_catalogue_file
from transit_odp.site_admin.constants import ARCHIVE_CATEGORY_FILENAME, DataCatalogue
from transit_odp.site_admin.models import DocumentArchive

logger = logging.getLogger(__name__)


@shared_task()
def task_create_data_catalogue_archive():
    filename = ARCHIVE_CATEGORY_FILENAME[DataCatalogue]
    buffer_ = create_data_catalogue_file()
    archive = File(buffer_, name=filename)

    logger.info("[DateCatalogue] Creating data catalogue export.")
    catalogue = (
        DocumentArchive.objects.filter(category=DataCatalogue)
        .order_by("modified")
        .last()
    )
    if catalogue is None:
        DocumentArchive.objects.create(archive=archive, category=DataCatalogue)
    else:
        catalogue.archive.save(filename, archive)
