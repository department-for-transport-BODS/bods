import zipfile
from datetime import timedelta
from pathlib import Path

import pytest
from django.utils import timezone
from freezegun import freeze_time

from transit_odp.browse.data_archive import change_data_archive
from transit_odp.organisation.factories import DatasetFactory, OrganisationFactory
from transit_odp.pipelines.models import ChangeDataArchive

pytestmark = pytest.mark.django_db


def test_output():
    """Tests the format of the outpath string"""
    # Setup
    now = timezone.now()

    # Test
    output = change_data_archive.get_outpath(now)

    # Assert
    assert output == f"/tmp/bodds_updates_{now.strftime('%Y%m%d')}.zip"


def test_get_datasets_published_at():
    """Tests the method returns datasets which have recently changed"""
    # Setup
    now = timezone.now()
    yesterday = now - timedelta(days=1)

    # Create a dataset (with a live_revision) this will have published_at = now
    DatasetFactory()

    # Create a dataset with a live_revision that was published yesterday
    with freeze_time(yesterday):
        expected = DatasetFactory()

    # Create a dataset published 2 days ago
    with freeze_time(now - timedelta(days=2)):
        DatasetFactory()

    # Test
    # archive all datasets which were published yesterday
    datasets = change_data_archive.get_datasets_published_at(yesterday)

    # Assert
    assert len(datasets) == 1
    assert datasets[0] == expected


def test_upload_change_data_archive(tmp_path):
    """Tests upload_bulk_data_archive creates BulkDataArchive with zipfile at outpath"""
    # Setup
    zipped = tmp_path / "changes.zip"
    zipped.write_text("Some data")

    # Test
    archive = change_data_archive.upload_change_data_archive(zipped, timezone.now())

    # Assert
    qs = ChangeDataArchive.objects.all()
    assert len(qs) == 1

    assert archive.published_at is not None
    with archive.data.open("r") as fin:
        assert fin.read() == "Some data"


def test_run():
    """End-to-end test of the bulk data archive pipeline"""
    # Setup
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    basename = f"bodds_updates_{yesterday.strftime('%Y%m%d')}"

    # Explicitly create organisation and dataset
    org = OrganisationFactory(short_name="Jackson LLC", id=2)
    DatasetFactory(organisation=org)

    # Create a dataset with a live_revision that was published yesterday
    with freeze_time(yesterday):
        expected = DatasetFactory(organisation=org)
        directory_name = f"{org.short_name}_{org.id}"

    # Create a dataset published 2 days ago
    with freeze_time(now - timedelta(days=2)):
        DatasetFactory(organisation=org)

    # Test
    change_data_archive.run()

    # Assert
    qs = ChangeDataArchive.objects.all()
    assert len(qs) == 1

    archive = qs[0]
    assert archive.published_at == yesterday.date()
    assert archive.data.name == f"{basename}.zip"

    with zipfile.ZipFile(archive.data, "r") as zf:
        assert zf.testzip() is None

        # assert archive contains name of the dataset
        upload = expected.live_revision.upload_file
        assert zf.namelist() == [f"{directory_name}/{upload.name}"]

        # Access zip file with upload filename
        with zf.open(Path(directory_name, upload.name).as_posix(), "r") as zipped:
            with upload.open("rb") as orig:
                # Test the upload file data can be read from the zip
                assert zipped.read() == orig.read()


def test_run_does_create_archive_if_no_changes():
    """Tests the pipeline returns without creating an archive if there are no changes"""
    # Test
    change_data_archive.run()

    # Assert
    assert not ChangeDataArchive.objects.exists()
