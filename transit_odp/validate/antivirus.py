import logging
from dataclasses import dataclass
from typing import BinaryIO, Optional

from clamd import BufferTooLongError, ClamdNetworkSocket
from clamd import ConnectionError as ClamdConnectionError
from tenacity import (
    before_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from transit_odp.validate.exceptions import ValidationException

logger = logging.getLogger(__name__)

SCAN_ATTEMPTS = 5
MULTIPLIER = 1


class AntiVirusError(ValidationException):
    """Base exception for antivirus scans."""

    code = "ANTIVIRUS_FAILURE"
    message_template = "Antivirus failed validating file {filename}."


class SuspiciousFile(AntiVirusError):
    """Exception for when a suspicious file is found."""

    code = "SUSPICIOUS_FILE"
    message_template = "Anti-virus alert triggered for file {filename}."


class ClamConnectionError(AntiVirusError):
    """Exception for when we can't connect to the ClamAV server."""

    code = "AV_CONNECTION_ERROR"
    message_template = "Could not connect to Clam daemon when testing {filename}."


@dataclass
class ScanResult:
    status: str
    reason: Optional[str] = None


class FileScanner:
    """Class used to scan for viruses.

    Args:
        host(str): Host path of ClamAV scannner.
        port(srt): Post of ClamAV scanner.

    Examples:
        >>> scanner = FileScanner("http://clamavhost.example", 9876)
        >>> f = open("suspect/file.zip", "rb")
        >>> scanner.scan(f)
        >>> f.close()

    Raises:
        ClamConnectionError: if cant connect to Clamd.
        AntiVirusError: if an error occurs during scanning.
        SuspiciousFile: if a suspicious file is found.

    """

    def __init__(self, host: str, port: int):
        """Scan f with ClamAV antivirus scanner"""
        logger.info("Antivirus scan: Started")
        self.clamav = ClamdNetworkSocket(host=host, port=port)

    @retry(
        reraise=True,
        retry=retry_if_exception_type(ClamConnectionError),
        wait=wait_random_exponential(multiplier=MULTIPLIER, max=10),
        stop=stop_after_attempt(SCAN_ATTEMPTS),
        before=before_log(logger, logging.DEBUG),
    )
    def scan(self, file_: BinaryIO):
        """
        Retrieves and returns the result of the scanned file. A maxiumum
        of 5 scan attempts will occur if a connection to ClamAV cannot be
        established (leading to ClamConnectionError exception).

        Args:
            file_: File being scanned
        """
        try:
            result = self._perform_scan(file_)
        except ClamdConnectionError as exc:
            logger.info("Issue wih ClamAV connection: Re-attempting connection.")
            raise ClamConnectionError(file_.name) from exc

        if result.status == "ERROR":
            logger.info("Antivirus scan: FAILED")
            raise AntiVirusError(file_.name)
        elif result.status == "FOUND":
            logger.exception("Antivirus scan: FOUND")
            raise SuspiciousFile(file_.name, result.reason)
        logger.info("Antivirus scan: OK")

    @retry(
        reraise=True,
        retry=retry_if_exception_type(TypeError),
        wait=wait_random_exponential(multiplier=MULTIPLIER, max=10),
        stop=stop_after_attempt(SCAN_ATTEMPTS),
        before=before_log(logger, logging.DEBUG),
    )
    def _perform_scan(self, file_: BinaryIO) -> ScanResult:
        """
        Returns response from ClamAV. A maxiumum of 5 scan attempts will occur
        if no response is received from ClamAV (leading to TypeError exception).

        Args:
            file_: File being scanned

        Returns:
            ScanResult: Result from response
        """

        try:
            response = self.clamav.instream(file_)
            status, reason = response["stream"]
            return ScanResult(status=status, reason=reason)
        except TypeError as exc:
            msg = "Issue with the ClamAV response: Re-requesting response."
            logger.info(msg)
            raise TypeError(exc)
        except BufferTooLongError as e:
            msg = "Antivirus scan failed due to BufferTooLongError"
            logger.exception(msg, exc_info=True)
            raise AntiVirusError(file_.name, message=msg) from e
