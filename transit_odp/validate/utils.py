import io
import zipfile
from typing import Optional


def filter_and_repackage_zip(intial_zip_file, files_to_remove):
    output_zip_stream = io.BytesIO()
    print("files_to_remove>>> ", files_to_remove)
    with zipfile.ZipFile(intial_zip_file, "r") as input_zip:
        with zipfile.ZipFile(output_zip_stream, "w") as output_zip:
            for file_info in input_zip.infolist():
                if (
                    file_info.filename.endswith(".xml")
                    and file_info.filename.split("/")[-1] not in files_to_remove
                ):
                    with input_zip.open(file_info.filename) as file:
                        file_data = file.read()
                        output_zip.writestr(file_info.filename, file_data)
    output_zip_stream.seek(0)
    return output_zip_stream


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
