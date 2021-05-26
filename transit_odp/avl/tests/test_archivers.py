import io
from datetime import datetime
from unittest.mock import Mock, patch
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from transit_odp.avl.archivers import GTFSRTArchiver
from transit_odp.avl.factories import GTFSRTDataArchiveFactory
from transit_odp.avl.models import CAVLDataArchive

pytestmark = pytest.mark.django_db

ARCHIVE_MODULE = "transit_odp.avl.archivers"


def test_filename():
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver(url)
    archiver._access_time = datetime(2020, 1, 1, 1, 1, 1)
    archiver._content = b"fakedata"
    expected_filename = "gtfsrt_2020-01-01_010101.zip"
    assert expected_filename == archiver.filename


def test_data_format_value():
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver(url)
    assert archiver.data_format_value == "gtfsrt"


def test_access_time_value_error():
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver(url)
    with pytest.raises(ValueError) as exc:
        archiver.access_time
        assert str(exc.value) == "`content` has not been fetched yet."


@patch(ARCHIVE_MODULE + ".requests")
def test_access_time(mrequests):
    mrequests.get.return_value = Mock(content=b"response")
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver(url)
    archiver.content
    assert archiver.access_time is not None


def test_content_filename():
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver(url)
    assert archiver.content_filename == "gtfsrt.bin"


def test_get_file():
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver(url)
    archiver._content = b"content"
    bytesio = archiver.get_file(archiver._content)

    expected = io.BytesIO()
    with ZipFile(expected, mode="w", compression=ZIP_DEFLATED) as zf:
        zf.writestr("gtfsrt.bin", archiver._content)

    expected.seek(0)
    bytesio.seek(0)
    assert expected.read() == bytesio.read()


def test_archive():
    url = "https://fakeurl.zz/datafeed"
    archiver = GTFSRTArchiver(url)

    content = b"newcontent"
    access_time = datetime(2020, 1, 1, 12, 1, 1)

    archiver._content = content
    archiver._access_time = access_time

    expected_name = f"gtfsrt_{access_time:%Y-%m-%d_%H%M%S}.zip"
    expected_content_name = "gtfsrt.bin"

    archiver._content = content
    archiver._access_time = access_time

    assert CAVLDataArchive.objects.count() == 0
    archiver.archive()
    assert CAVLDataArchive.objects.count() == 1
    archive = CAVLDataArchive.objects.last()
    assert archive.data_format == CAVLDataArchive.GTFSRT
    with archive.data.open("rb") as f:
        assert f.name == expected_name
        with ZipFile(f, "r") as zf:
            assert [expected_content_name] == zf.namelist()
            with zf.open(expected_content_name) as gtfs:
                assert gtfs.read() == content


def test_archive_if_existing_file():
    url = "https://fakeurl.zz/datafeed"
    GTFSRTDataArchiveFactory()
    archiver = GTFSRTArchiver(url)

    content = b"newcontent"
    access_time = datetime(2020, 1, 1, 12, 1, 1)

    archiver._content = content
    archiver._access_time = access_time

    expected_name = f"gtfsrt_{access_time:%Y-%m-%d_%H%M%S}.zip"
    expected_content_name = "gtfsrt.bin"

    assert CAVLDataArchive.objects.count() == 1
    archiver.archive()
    assert CAVLDataArchive.objects.count() == 1
    archive = CAVLDataArchive.objects.last()
    assert archive.data_format == CAVLDataArchive.GTFSRT
    with archive.data.open("rb") as f:
        assert f.name == expected_name
        with ZipFile(f, "r") as zf:
            assert [expected_content_name] == zf.namelist()
            with zf.open(expected_content_name) as gtfs:
                assert gtfs.read() == content
