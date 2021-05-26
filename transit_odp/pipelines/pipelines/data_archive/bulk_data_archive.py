import os
import zipfile
from shutil import copyfileobj

from celery.utils.log import get_task_logger
from django.core.files import File
from django.utils import timezone

from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset
from transit_odp.pipelines.models import BulkDataArchive

logger = get_task_logger(__name__)


def get_datasets(dataset_type: DatasetType):
    """Returns all active datasets, i.e. status != expired."""
    return (
        Dataset.objects.get_active_org()
        .filter(dataset_type=dataset_type)
        .get_active()
        .select_related("live_revision")
    )


def get_outpath(dataset_type: DatasetType):
    now = timezone.now().strftime("%Y%m%d")
    if dataset_type == DatasetType.FARES.value:
        return f"/tmp/bodds_fares_archive_{now}.zip"
    else:
        return f"/tmp/bodds_archive_{now}.zip"


def zip_datasets(datasets, outpath):
    """Zips the uploaded data in `datasets` into the archive `outpath`"""
    logger.info(
        f"[bulk_data_archive] creating zip of {len(datasets)} datasets at {outpath}"
    )
    # Get the name of the zip to use of the parent directory in the zip.
    inner_directory = os.path.splitext(os.path.basename(outpath))[0]
    with zipfile.ZipFile(outpath, "w") as zf:
        for dataset in datasets:
            upload = dataset.live_revision.upload_file
            # Open dataset upload file
            with upload.open("rb") as fin:
                # Write files into inner directory to keep all the files together
                # when the user unzips
                with zf.open(os.path.join(inner_directory, upload.name), "w") as fout:
                    # efficiently copy data from fin into fout
                    copyfileobj(fin, fout)


def upload_bulk_data_archive(outpath, dataset_type: DatasetType):
    """Saves the zip file at `outpath` to the BulkDataArchive model and uploads the
    zip to the MEDIA_ROOT"""
    logger.info("[bulk_data_archive] creating BulkDataArchive record")
    with open(outpath, "rb") as fin:
        archive = BulkDataArchive.objects.create(
            data=File(fin, name=os.path.basename(outpath)), dataset_type=dataset_type
        )
    return archive


def create_timetable_archive():
    # Timetable Bulk data archive
    logger.info("[bulk_data_archive] processing Timetable data")

    dataset_type = DatasetType.TIMETABLE.value

    # Get active datasets
    timetable_datasets = get_datasets(dataset_type=dataset_type)

    # Get local path to create zip file
    output = get_outpath(dataset_type=dataset_type)

    # Write copy each dataset's upload_file into the zip
    zip_datasets(timetable_datasets, output)

    # Create BulkDataArchive
    timetable_archive = upload_bulk_data_archive(output, dataset_type=dataset_type)

    logger.info(f"[bulk_data_archive] created for timetables: {timetable_archive}")


def create_fares_archive():
    # Fares Bulk data archive
    logger.info("[bulk_data_archive] processing Fares data")

    dataset_type = DatasetType.FARES.value

    # Get active datasets
    fares_datasets = get_datasets(dataset_type=dataset_type)

    # Get local path to create zip file
    output = get_outpath(dataset_type=dataset_type)

    # Write copy each dataset's upload_file into the zip
    zip_datasets(fares_datasets, output)

    # Create BulkDataArchive
    fares_archive = upload_bulk_data_archive(output, dataset_type=dataset_type)

    logger.info(f"[bulk_data_archive] created for fares: {fares_archive}")


def run():
    logger.info("[bulk_data_archive] called")
    # Note this task requires the set_expired_datasets task to run first to ensure the
    # bulk download is consistent.
    # TODO We could create a higher-level Celery task to run the series of tasks in
    # order: set expired -> bulk download

    create_timetable_archive()

    create_fares_archive()
