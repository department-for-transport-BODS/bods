import os
from datetime import datetime, timedelta

from celery.utils.log import get_task_logger
from django.core.files import File
from django.db.models.functions import TruncDate
from django.utils import timezone

from transit_odp.organisation.constants import DatasetType
from transit_odp.pipelines.models import ChangeDataArchive
from transit_odp.pipelines.pipelines.data_archive.bulk_data_archive import (
    get_datasets,
    zip_datasets,
)

logger = get_task_logger(__name__)


def get_outpath(date: datetime):
    datestr = date.strftime("%Y%m%d")
    return f"/tmp/bodds_updates_{datestr}.zip"


def get_datasets_published_at(date: datetime):
    # Get all active datasets (are published and not expired)
    datasets = get_datasets(dataset_type=DatasetType.TIMETABLE.value)

    # Filter datasets to those which were published yesterday. Note this task
    # is intended to be run at night and produce an archive of all the changes for
    # the day before.
    datasets = datasets.annotate(
        date_published_at=TruncDate("live_revision__published_at")
    ).filter(date_published_at=date)

    return datasets


def upload_change_data_archive(outpath, published_at):
    """Saves the zip file at `outpath` to the BulkDataArchive model and uploads the
    zip to the MEDIA_ROOT"""
    logger.info("[change_data_archive] creating ChangeDataArchive record")
    with open(outpath, "rb") as fin:
        archive = ChangeDataArchive.objects.create(
            data=File(fin, name=os.path.basename(outpath)), published_at=published_at
        )
    return archive


def run():
    logger.info("[change_data_archive] called")

    # Get date to build archive
    yesterday = timezone.now().date() - timedelta(days=1)

    if ChangeDataArchive.objects.filter(published_at=yesterday).count() > 0:
        logger.info(
            f"[change_data_archive] Archive already exists for {yesterday}. "
            "No new archive will be created."
        )
        return

    # Get active datasets
    datasets = get_datasets_published_at(yesterday)

    if len(datasets) == 0:
        logger.info(
            "[change_data_archive] found no datasets that were published "
            f"on {yesterday}. No archive will be created."
        )
        return

    # Get local path to create zip file
    output = get_outpath(yesterday)

    # Write copy each dataset's upload_file into the zip
    zip_datasets(datasets, output)

    # Create BulkDataArchive
    archive = upload_change_data_archive(output, yesterday)

    logger.info(f"[change_data_archive] created {archive}")
