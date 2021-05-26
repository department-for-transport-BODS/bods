from zipfile import ZIP_DEFLATED

import pytest
from requests import Response

from transit_odp.validate.tests.utils import create_sparse_file, create_zip_file
from transit_odp.validate.utils import bytes_are_zip_file, get_filetype_from_response


def test_bytes_are_zip_file_true(tmp_path):
    """Test if file is a zip from bytes given file is a zip."""
    file1 = tmp_path / "file1.xml"
    create_sparse_file(file1, 100)

    zipfilepath = tmp_path / "testzip.zip"
    create_zip_file(zipfilepath, [file1], compression=ZIP_DEFLATED)

    with open(zipfilepath, "rb") as f:
        assert bytes_are_zip_file(f.read())


def test_bytes_are_zip_file_false(tmp_path):
    """Test if file is a zip from bytes given file is an xml."""
    file1 = tmp_path / "file1.xml"
    create_sparse_file(file1, 100)

    with open(file1, "rb") as f:
        assert not bytes_are_zip_file(f.read())


@pytest.mark.parametrize(
    "content_type,expected",
    [("text/xml", "xml"), ("", None), ("application/zip", "zip")],
)
def test_get_file_type_from_response_content_type(content_type, expected, mocker):
    """Test for getting the file type using the Content-Type."""
    headers = {"Content-Type": content_type}
    response = mocker.Mock(spec=Response, headers=headers, content=None)
    actual = get_filetype_from_response(response)
    assert actual is expected


def test_get_file_type_by_bytes(tmp_path, mocker):
    """Test given that Content-Type is "" and content is a zipfile bytes."""
    file1 = tmp_path / "file1.xml"
    create_sparse_file(file1, 100)
    zipfilepath = tmp_path / "testzip.zip"
    create_zip_file(zipfilepath, [file1], compression=ZIP_DEFLATED)

    with open(zipfilepath, "rb") as f:
        response = mocker.Mock(spec=Response, headers={}, content=f.read())
        actual = get_filetype_from_response(response)
        assert actual == "zip"
