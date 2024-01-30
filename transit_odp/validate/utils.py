import io
import zipfile
from typing import Optional


def get_file_size(file_):
    """Returns the file_size"""

    # This only works if the file exists on the file system. For in-memory streams,
    # such as processing memebrs of a zip file, fileno is not available
    # size = os.fstat(_f.fileno()).st_size
    # _f.seek(0)

    # seek end of file then get the size by reading position
    file_.seek(0, 2)
    size = file_.tell()

    # search start of file
    file_.seek(0)

    return size


def bytes_are_zip_file(content: bytes):
    """Returns true if bytes are a zipfile."""
    return zipfile.is_zipfile(io.BytesIO(content))


def get_filetype_from_response(response) -> Optional[str]:
    content_type = response.headers.get("Content-Type", "")
    if "zip" in content_type or bytes_are_zip_file(response.content):
        return "zip"

    if "xml" in content_type:
        return "xml"

    return None
