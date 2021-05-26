from zipfile import ZIP_DEFLATED

import pytest

from transit_odp.validate.tests.utils import create_sparse_file, create_zip_file
from transit_odp.validate.zip import (
    NestedZipForbidden,
    NoDataFound,
    ZippedValidator,
    ZipTooLarge,
)


@pytest.mark.parametrize(
    "file_size,limit,expected",
    [(int(1e7), int(1e5), True), (int(1e3), int(1e5), False)],
)
def test_is_too_large(file_size, limit, expected, tmp_path):
    big_file = tmp_path / "bigfile.txt"
    create_sparse_file(big_file, file_size)

    zip_filename = tmp_path / "testfile.zip"
    create_zip_file(zip_filename, [big_file])

    with open(zip_filename, "rb") as f, ZippedValidator(f, limit) as zipped:
        assert zipped.is_too_large() == expected


def test_is_nested_zip_false(tmp_path):
    file1 = tmp_path / "file1.txt"
    create_sparse_file(file1, 10)

    zip_filename = tmp_path / "testzip.zip"
    create_zip_file(zip_filename, [file1])
    with open(zip_filename, "rb") as f, ZippedValidator(f) as zipped:
        assert not zipped.is_nested_zip()


def test_is_nested_zip_true(tmp_path):
    file1 = tmp_path / "file1.txt"
    create_sparse_file(file1, 10)

    zip_filename = tmp_path / "testfile.zip"
    create_zip_file(zip_filename, [file1])

    nested_filename = tmp_path / "nestedzip.zip"
    create_zip_file(nested_filename, [zip_filename])

    with open(nested_filename, "rb") as f, ZippedValidator(f) as zipped:
        assert zipped.is_nested_zip()

        with pytest.raises(NestedZipForbidden) as excinfo:
            zipped.validate()
        assert str(nested_filename) == excinfo.value.filename


@pytest.mark.parametrize("file_ext, expected", [(".txt", False), (".xml", True)])
def test_has_data(file_ext, expected, tmp_path):
    """Test if zip contains files with xml extension.

    This does not validate whether the xml is valid.
    """
    file1 = tmp_path / f"file1{file_ext}"
    create_sparse_file(file1, 10)

    zip_filename = tmp_path / "testfile.zip"
    create_zip_file(zip_filename, [file1])

    with open(zip_filename, "rb") as f, ZippedValidator(f) as zipped:
        assert zipped.has_data() == expected


def test_validate_has_no_data(tmp_path):

    zip_filename = tmp_path / "testfile.zip"
    create_zip_file(zip_filename, [])

    with open(zip_filename, "rb") as f, ZippedValidator(f) as zipped:
        with pytest.raises(NoDataFound):
            zipped.validate()


@pytest.mark.parametrize(
    "file_size,limit,expected",
    [
        (int(1e7), int(1e5), True),
        (int(1e3), int(1e3), True),
        (int(1e2), int(1e5), False),
    ],
)
def test_exceeds_uncompressed_size(file_size, limit, expected, tmp_path):
    """Tests if uncompressed file size exceeds the max_file_size."""
    files = ["file1.xml", "file2.xml"]
    files = [tmp_path / f for f in files]
    for filename in files:
        create_sparse_file(filename, file_size)

    zip_filename = tmp_path / "testfile.zip"
    create_zip_file(zip_filename, files, compression=ZIP_DEFLATED)

    with open(zip_filename, "rb") as f, ZippedValidator(f, limit) as zipped:
        assert zipped.exceeds_uncompressed_size() == expected


def test_validate_zip_too_large(tmp_path):
    files = ["file1.xml", "file2.xml"]
    files = [tmp_path / f for f in files]
    for filename in files:
        create_sparse_file(filename, int(1e5))

    zip_filename = tmp_path / "testfile.zip"
    create_zip_file(zip_filename, files, compression=ZIP_DEFLATED)

    with open(zip_filename, "rb") as f, ZippedValidator(f, 2e5) as zipped:
        with pytest.raises(ZipTooLarge):
            zipped.validate()


@pytest.mark.parametrize(
    "filenames,expected_len", [(["file1.xml", "file2.xml", "file3.txt"], 2), ([], 0)]
)
def test_get_files(filenames, expected_len, tmp_path):
    """Test that get_files returns correct files"""

    files = [tmp_path / name for name in filenames]
    for filename in files:
        create_sparse_file(filename, int(1e2))

    zip_filename = tmp_path / "testfile.zip"
    create_zip_file(zip_filename, files)

    with open(zip_filename, "rb") as f, ZippedValidator(f, 1e6) as zipped:
        assert len(zipped.get_files()) == expected_len
