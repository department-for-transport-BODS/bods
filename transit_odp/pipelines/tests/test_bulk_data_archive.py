import os
import zipfile
from datetime import datetime

import pytest
from django.test import override_settings
from django.utils import timezone

from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.factories import DatasetFactory, OrganisationFactory
from transit_odp.pipelines.models import BulkDataArchive
from transit_odp.pipelines.pipelines.data_archive import bulk_data_archive

pytestmark = pytest.mark.django_db

mut = "transit_odp.pipelines.pipelines.data_archive.bulk_data_archive"


def test_get_datasets(mocker):
    """Tests get_datasets returns active datasets"""
    mocked = mocker.patch(f"{mut}.Dataset")
    bulk_data_archive.get_datasets(dataset_type=DatasetType.TIMETABLE.value)
    bulk_data_archive.get_datasets(dataset_type=DatasetType.FARES.value)
    assert mocked.objects.get_active_org.call_count == 2


def test_output():
    """Tests the format of the outpath string"""
    # Setup
    now = timezone.now().strftime("%Y%m%d")

    # Test
    timetable_output = bulk_data_archive.get_outpath(
        dataset_type=DatasetType.TIMETABLE.value
    )
    fares_output = bulk_data_archive.get_outpath(dataset_type=DatasetType.FARES.value)

    # Assert
    assert timetable_output == f"/tmp/bodds_archive_{now}.zip"
    assert fares_output == f"/tmp/bodds_fares_archive_{now}.zip"


def test_zip_timetable_datasets(tmp_path):
    """Tests the zip_datasets method"""
    datasets = DatasetFactory.create_batch(
        5, live_revision__upload_file__data=b"Test data"
    )

    # get temporary outpath
    outpath = str(tmp_path / "bulk.zip")

    # Test
    bulk_data_archive.zip_datasets(datasets, outpath)

    # Assert
    with zipfile.ZipFile(outpath, "r") as zf:
        assert zf.testzip() is None

        for dataset in datasets:
            upload = dataset.live_revision.upload_file
            # Access zip file with upload filename
            with zf.open(os.path.join("bulk", upload.name), "r") as zipped:
                with upload.open("rb") as orig:
                    # Test the upload file data can be read from the zip
                    assert zipped.read() == orig.read()


def test_zip_fares_datasets(tmp_path):
    """Tests the zip_datasets method"""
    datasets = DatasetFactory.create_batch(
        5,
        live_revision__upload_file__data=b"Test data",
        dataset_type=DatasetType.FARES.value,
    )

    # get temporary outpath
    outpath = str(tmp_path / "bulk.zip")

    # Test
    bulk_data_archive.zip_datasets(datasets, outpath)

    # Assert
    with zipfile.ZipFile(outpath, "r") as zf:
        assert zf.testzip() is None

        for dataset in datasets:
            upload = dataset.live_revision.upload_file
            # Access zip file with upload filename
            with zf.open(os.path.join("bulk", upload.name), "r") as zipped:
                with upload.open("rb") as orig:
                    # Test the upload file data can be read from the zip
                    assert zipped.read() == orig.read()


def test_bulk_archive_creates_3_files():
    """
    Tests upload_bulk_data_archive creates 3 archive files - Timetable, compliant
    Timetable and Fares.
    """
    bulk_data_archive.run()
    qs = BulkDataArchive.objects.all()
    assert len(qs) == 3


def test_upload_timetable_bulk_data_archive(tmp_path):
    """Tests upload_bulk_data_archive creates BulkDataArchive with zipfile at outpath"""
    # Setup
    zipped = tmp_path / "bulk.zip"
    zipped.write_text("Some data")

    # Test
    bulk_data_archive.upload_bulk_data_archive(
        zipped, dataset_type=DatasetType.TIMETABLE.value
    )

    # Assert
    qs = BulkDataArchive.objects.filter(dataset_type=DatasetType.TIMETABLE.value)
    assert len(qs) == 1

    archive = qs[0]
    with archive.data.open("r") as fin:
        assert fin.read() == "Some data"


def test_upload_fares_bulk_data_archive(tmp_path):
    """Tests upload_bulk_data_archive creates BulkDataArchive with zipfile at outpath"""
    # Setup
    zipped = tmp_path / "bulk.zip"
    zipped.write_text("Some data")

    # Test
    bulk_data_archive.upload_bulk_data_archive(
        zipped, dataset_type=DatasetType.FARES.value
    )

    # Assert
    qs = BulkDataArchive.objects.filter(dataset_type=DatasetType.FARES.value)
    assert len(qs) == 1

    archive = qs[0]
    with archive.data.open("r") as fin:
        assert fin.read() == "Some data"


@override_settings(PTI_START_DATE=datetime(2021, 4, 1))
def test_timetable_bulk_data_archive():
    """End-to-end test of the bulk data archive pipeline"""
    # Setup
    now = timezone.now().strftime("%Y%m%d")
    basename = f"bodds_archive_{now}"

    datasets = DatasetFactory.create_batch(
        5,
        live_revision__upload_file__data=b"Test data",
        dataset_type=DatasetType.TIMETABLE.value,
        created=datetime(2021, 3, 1),
    )

    # Test
    bulk_data_archive.run()

    # Assert
    qs = BulkDataArchive.objects.filter(
        dataset_type=DatasetType.TIMETABLE.value, compliant_archive=False
    )
    assert len(qs) == 1

    archive = qs[0]
    assert archive.data.name == f"{basename}.zip"

    with zipfile.ZipFile(archive.data, "r") as zf:
        assert zf.testzip() is None

        # assert archive contains names of each dataset
        expected_names = [
            f"{basename}/{dataset.live_revision.upload_file.name}"
            for dataset in datasets
        ]
        for name in zf.namelist():
            assert name in expected_names

        for dataset in datasets:
            upload = dataset.live_revision.upload_file
            # Access zip file with upload filename
            with zf.open(os.path.join(basename, upload.name), "r") as zipped:
                with upload.open("rb") as orig:
                    # Test the upload file data can be read from the zip
                    assert zipped.read() == orig.read()


def test_fares_bulk_data_archive():
    """End-to-end test of the bulk data archive pipeline"""
    # Setup
    now = timezone.now().strftime("%Y%m%d")
    basename = f"bodds_fares_archive_{now}"

    datasets = DatasetFactory.create_batch(
        5,
        live_revision__upload_file__data=b"Test data",
        dataset_type=DatasetType.FARES.value,
    )

    # Test
    bulk_data_archive.run()

    # Assert
    qs = BulkDataArchive.objects.filter(dataset_type=DatasetType.FARES.value)
    assert len(qs) == 1

    archive = qs[0]
    assert archive.data.name == f"{basename}.zip"

    with zipfile.ZipFile(archive.data, "r") as zf:
        assert zf.testzip() is None

        # assert archive contains names of each dataset
        expected_names = [
            f"{basename}/{dataset.live_revision.upload_file.name}"
            for dataset in datasets
        ]
        for name in zf.namelist():
            assert name in expected_names

        for dataset in datasets:
            upload = dataset.live_revision.upload_file
            # Access zip file with upload filename
            with zf.open(os.path.join(basename, upload.name), "r") as zipped:
                with upload.open("rb") as orig:
                    # Test the upload file data can be read from the zip
                    assert zipped.read() == orig.read()


@override_settings(PTI_START_DATE=datetime(2021, 4, 1))
def test_bulk_data_archive_not_adding_dataset_with_inactive_org():
    """End-to-end test of the bulk data archive pipeline"""
    # Setup
    now = timezone.now().strftime("%Y%m%d")
    basename = f"bodds_archive_{now}"

    org1 = OrganisationFactory.create(is_active=False)

    DatasetFactory.create_batch(
        5,
        live_revision__upload_file__data=b"Test data1",
        organisation=org1,
        created=datetime(2021, 5, 1),
    )

    # Test
    bulk_data_archive.run()

    # Assert
    qs = BulkDataArchive.objects.filter(
        dataset_type=DatasetType.TIMETABLE.value, compliant_archive=False
    )
    assert len(qs) == 1

    archive = qs[0]
    assert archive.data.name == f"{basename}.zip"

    with zipfile.ZipFile(archive.data, "r") as zf:
        assert zf.testzip() is None

        assert zf.namelist() == []


@override_settings(PTI_START_DATE=datetime(2021, 4, 1))
def test_compliant_timetable_bulk_data_archive():
    """End-to-end test of the bulk data archive pipeline"""
    # Setup
    now = timezone.now().strftime("%Y%m%d")
    basename = f"bodds_compliant_timetables_archive_{now}"

    datasets = DatasetFactory.create_batch(
        5,
        live_revision__upload_file__data=b"Test data",
        dataset_type=DatasetType.TIMETABLE.value,
        created=datetime(2021, 5, 1),
    )

    # Test
    bulk_data_archive.run()

    # Assert
    qs = BulkDataArchive.objects.filter(
        dataset_type=DatasetType.TIMETABLE.value, compliant_archive=True
    )

    assert len(qs) == 1

    archive = qs[0]
    assert archive.data.name == f"{basename}.zip"

    with zipfile.ZipFile(archive.data, "r") as zf:
        assert zf.testzip() is None

        # assert archive contains names of each dataset
        expected_names = [
            f"{basename}/{dataset.live_revision.upload_file.name}"
            for dataset in datasets
        ]
        for name in zf.namelist():
            assert name in expected_names

        for dataset in datasets:
            upload = dataset.live_revision.upload_file
            # Access zip file with upload filename
            with zf.open(os.path.join(basename, upload.name), "r") as zipped:
                with upload.open("rb") as orig:
                    # Test the upload file data can be read from the zip
                    assert zipped.read() == orig.read()
