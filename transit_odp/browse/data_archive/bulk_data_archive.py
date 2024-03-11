import logging
import os
import zipfile
from collections import defaultdict
from pathlib import Path
from shutil import copyfileobj

from celery.utils.log import get_task_logger
from django.core.files import File
from django.utils import timezone

from transit_odp.organisation.constants import (
    DatasetType,
    TimetableType,
    TravelineRegions,
)
from transit_odp.organisation.models import Dataset
from transit_odp.pipelines.models import BulkDataArchive

logger = get_task_logger(__name__)


def get_datasets(dataset_type: DatasetType):
    """Returns all active datasets, i.e. status != expired."""
    return (
        Dataset.objects.get_active_org()
        .filter(dataset_type=dataset_type)
        .get_active()
        .select_related("organisation", "live_revision")
    )


def get_datasets_by_region(region_code: str):
    """Returns all published distinct datasets by region."""
    return (
        Dataset.objects.get_active_org()
        .filter(live_revision__admin_areas__traveline_region_id=region_code)
        .filter(dataset_type=TimetableType)
        .get_only_active_datasets_bulk_archive()
        .distinct("id")
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
    orgs = defaultdict(list)
    for dataset in datasets:
        org = dataset.organisation
        orgs[f"{org.short_name}_{org.id}"].append(dataset)

    with zipfile.ZipFile(outpath, "w") as zf:
        for directory_name, datasets in orgs.items():
            for dataset in datasets:
                upload = dataset.live_revision.upload_file
                # Open dataset upload file
                with upload.open("rb") as fin:
                    relative_path_upload_file = Path(directory_name, upload.name)
                    # Write files into inner directory to keep all the files together
                    # when the user unzips
                    with zf.open(
                        relative_path_upload_file.as_posix(),
                        "w",
                    ) as fout:
                        # efficiently copy data from fin into fout
                        copyfileobj(fin, fout)


def upload_bulk_data_archive(
    outpath,
    dataset_type: DatasetType,
    is_compliant: bool = False,
    traveline_regions: str = "All",
):
    """Saves the zip file at `outpath` to the BulkDataArchive model and uploads the
    zip to the MEDIA_ROOT"""
    logger.info("[bulk_data_archive] creating BulkDataArchive record")
    with open(outpath, "rb") as fin:
        archive = BulkDataArchive.objects.create(
            data=File(fin, name=os.path.basename(outpath)),
            dataset_type=dataset_type,
            compliant_archive=is_compliant,
            traveline_regions=traveline_regions,
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


def create_region_archive(region_code):
    logger.info("[bulk_data_archive] processing Timetables data by region")

    dataset_type = TimetableType

    # Get active datasets
    timetables_datasets = get_datasets_by_region(region_code)

    # Get local path to create zip file
    output = get_outpath(dataset_type=dataset_type)

    # Write copy each dataset's upload_file into the zip
    zip_datasets(timetables_datasets, output)

    # Create BulkDataArchive
    timetables_archive = upload_bulk_data_archive(
        output, dataset_type=dataset_type, traveline_regions=region_code
    )

    logger.info(
        f"[bulk_data_archive] created {timetables_archive} for the region {region_code}"
    )


def run():
    logger.info("[bulk_data_archive] called")
    # Note this task requires the set_expired_datasets task to run first to ensure the
    # bulk download is consistent.
    # TODO We could create a higher-level Celery task to run the series of tasks in
    # order: set expired -> bulk download

    create_timetable_archive()

    create_fares_archive()

    for t in TravelineRegions:
        if t != TravelineRegions.ALL:
            create_region_archive(t.value)
