import datetime
from typing import Optional


class PipelineException(Exception):
    """Basic exception for errors raised by a pipeline"""

    # TODO - add context from the Celery job, e.g. revision_id, task_name, etc.

    def __init__(self, message: Optional[str] = None):
        if message is None:
            # Set some default error message
            message = "An error occurred in the pipeline"
        super().__init__(message)


# File Errors


class FileError(PipelineException):
    """Base exception for errors raised by validating user uploaded files"""

    filename: str

    def __init__(self, filename: str, message: Optional[str] = None):
        if message is None:
            # Set some default useful error message
            message = f"An error occurred with file {filename}"
        super().__init__(message)
        self.filename = filename


class FileTooLarge(FileError):
    """The file size is too large"""


class ZipTooLarge(FileError):
    """The size of the uncompressed zip file is too large"""


class NestedZipForbidden(FileError):
    """The zip file must not contain nested zip files"""


class NoDataFoundError(FileError):
    """The zip file contained no TransXChange data"""


# XML Parse Errors


class XMLSyntaxError(FileError):
    """A document contained malformed XML"""


class DangerousXMLError(FileError):
    """A document contained dangerous XML constructs"""


# Validation Errors


class SchemaVersionMissing(FileError):
    """A document did not contain a schema version"""

    def __init__(self, filename: str):
        super().__init__(
            filename,
            message=(
                "Missing schema. Document must define a valid "
                "SchemaVersion attribute. Valid values = 2.1 or 2.4."
            ),
        )


class SchemaVersionNotSupported(FileError):
    """A document contained an unsupported schema version"""

    schema_version: str

    def __init__(self, filename: str, schema_version: str):
        super().__init__(
            filename,
            message=(
                f"Invalid schema version '{schema_version}'. Document must "
                f"define a valid SchemaVersion attribute with a value = 2.1 or 2.4."
            ),
        )
        self.schema_version = schema_version


class SchemaError(FileError):
    """A document failed schema validation"""

    schema_version: str

    def __init__(self, filename: str, schema_version: str):
        super().__init__(
            filename,
            message=(
                f"File {filename} is not compliant with schema "
                f"http://www.transxchange.org.uk version {schema_version}"
            ),
        )
        self.schema_version = schema_version


class DatasetExpired(FileError):
    """A document has already expired"""

    service_code: str
    expired_date: datetime.datetime

    def __init__(
        self, filename: str, service_code: str, expired_date: datetime.datetime
    ):
        super().__init__(
            filename,
            message=(
                f"File {filename} has contains expired service "
                f"'{service_code}' (expired at: {expired_date}). "
            ),
        )
        self.service_code = service_code
        self.expired_date = expired_date


class SuspiciousFile(FileError):
    """The file triggered an anti-virus alert"""

    reason: str

    def __init__(self, filename: str, reason: str):
        super().__init__(
            filename,
            message=(
                f"File {filename} has triggered an anti-virus alert. "
                f"FOUND: '{reason}'."
            ),
        )
        self.reason = reason
