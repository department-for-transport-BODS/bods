import logging
from zipfile import ZipFile, is_zipfile

from transit_odp.validate.exceptions import ValidationException
from transit_odp.validate.utils import get_file_size

logger = logging.getLogger(__name__)


class ZipValidationException(ValidationException):
    code = "ZIP_VALIDATION_FAILED"
    message_template = "Unable to validate zip {filename}."


class NestedZipForbidden(ZipValidationException):
    code = "NESTED_ZIP_FORBIDDEN"
    message_template = "Zip file {filename} contains another zip file."


class ZipTooLarge(ZipValidationException):
    code = "ZIP_TOO_LARGE"
    message_template = "Zip file {filename} is too large."


class NoDataFound(ZipValidationException):
    message_template = "Zip file {filename} contains no data files"
    code = "NO_DATA_FOUND"


class ZippedValidator:
    """Class for validating a transxchange zip file.

    Args:
        file (File): a zip file that requires validation.
        max_file_size (int): maximum size a file can be and pass validation.

    Examples:
        # Use the validator to basic validation, e.g. file size, nesting
        >>> f = open("path/to/zip/file.zip", "rb")
        >>> validator = ZippedValidator(f)
        >>> validator.validate()
        >>> f.close()
    """

    def __init__(self, file, max_file_size=5e9, data_file_ext=".xml"):
        self.file = file
        self.file.seek(0)
        self.max_file_size = max_file_size
        self.data_file_ext = data_file_ext
        self.zip_file = ZipFile(self.file)

    def __enter__(self):
        self.zip_file = ZipFile(self.file)
        return self

    def __exit__(self, *args):
        self.zip_file.close()

    def is_valid(self):
        try:
            self.validate()
        except ValidationException:
            return False

        return True

    def validate(self):
        """Validates a zip file and raises an exception if file is invalid.

        Raises:
            NestedZipForbidden: if zip file contains another zip file.
            ZipTooLarge: if zip file or sum of uncompressed files are
            greater than max_file_size.
            NoDataFound: if zip file contains no files with data_file_ext extension.
        """
        if self.is_nested_zip():
            raise NestedZipForbidden(self.file.name)

        if self.is_too_large() or self.exceeds_uncompressed_size():
            raise ZipTooLarge(self.file.name)

        if not self.has_data():
            raise NoDataFound(self.file.name)

    def is_too_large(self):
        """Returns True if zip file is greater than max_file_size."""
        return get_file_size(self.file) > self.max_file_size

    def is_nested_zip(self):
        """Returns True if zip file contains another zip file."""
        names = self.get_files(extension=".zip")
        # explicity check is_zipfile not just the extension
        for name in names:
            with self.open(name) as m:
                if name.endswith(".zip") or is_zipfile(m):
                    return True
        return False

    def has_data(self):
        """Returns True if zip file contains a file with an data_file_ext extension."""
        return len(self.get_files(extension=self.data_file_ext)) > 0

    def exceeds_uncompressed_size(self):
        """Returns True if the sum of the uncompressed files exceeds max_file_size."""
        total = sum([zinfo.file_size for zinfo in self.zip_file.filelist])
        return total > self.max_file_size

    def open(self, name):
        """Opens zip_file."""
        return self.zip_file.open(name, "r")

    def get_files(self, extension=".xml"):
        """Returns a list of the full paths to the files in zip file.

        Args:
            extension (str): The extension to filter the files on.

        """
        return [name for name in self.zip_file.namelist() if name.endswith(extension)]
