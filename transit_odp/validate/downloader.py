from dataclasses import dataclass

import requests

from transit_odp.validate.utils import get_filetype_from_response


class DownloadException(Exception):
    """An ambigious exception occurred during the request.

    Args:
        url (str): The url that was being accessed.
    """

    code = "DOWNLOAD_EXCEPTION"
    message_template = "Unable to download data from {url}."

    def __init__(self, url, message=None):
        self.url = url
        if message is None:
            self.message = self.message_template.format(url=url)
        else:
            self.message = message


class DownloadTimeout(DownloadException):
    """A request timed out."""

    code = "DOWNLOAD_TIMEOUT"
    message_template = "Request to {url} timed out."


class PermissionDenied(DownloadException):
    """A permission denied response was received."""

    code = "PERMISSION_DENIED"
    message_template = "Permission to access {url} denied."


class UnknownFileType(DownloadException):
    """The content returned in the response was of an unknown file type."""

    code = "UNKNOWN_FILE_TYPE"
    message_template = "File downloaded from {url} is not a zip or xml"


@dataclass
class DownloaderResponse:
    filetype: str
    content: bytes


class DataDownloader:
    """Class to download data files from a url.

    Args:
        url (str): the url hosting the file to download.
        username (str | None): optional username if url requires authentication.
        password (str | None): optional password if url requires authentication.

    Examples:
        # Use download the contents of the url and get the file format.
        >>> downloader = DataDownloader("https://fakeurl.com")
        >>> response = downloader.get()
        >>> response.filetype
            "xml"
        >>> response.content
            b"<Root><Child>hello,world</Child></Root>"
    """

    def __init__(self, url, username=None, password=None):
        self.url = url
        self.password = password
        self.username = username

    def raise_for_status(self, response):
        """Check the requests.Response code and raise a downloader exception.

        Args:
            response (Response): a requests.Response object.

        Raises:
            PermissionDenied: if status_code is 401 or 403
            DownloadException: if status_code is greater than 400 but not 401 or 403.

        """
        status_code = response.status_code
        if status_code in [401, 403]:
            raise PermissionDenied(self.url)
        elif status_code > 400:
            message = f"Unable to download from {self.url} with code {status_code}."
            raise DownloadException(self.url, message)

    def _make_request(self, method, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = 30

        if self.username is None or self.password is None:
            auth = None
        else:
            auth = (self.username, self.password)

        try:
            response = requests.request(method, self.url, auth=auth, **kwargs)
        except requests.Timeout as exc:
            raise DownloadTimeout(self.url) from exc
        except requests.RequestException as exc:
            raise DownloadException(self.url) from exc
        else:
            self.raise_for_status(response)
            return response

    def get(self, **kwargs) -> DownloaderResponse:
        """Get the response content.

        Args:
            kwargs (dict): Keyword arguments that are passed to requests.request.

        Raises:
            UnknownFileType: if filetype is not xml or zip.
        """
        response = self._make_request("GET", **kwargs)
        if (filetype := get_filetype_from_response(response)) is None:
            raise UnknownFileType(self.url)

        return DownloaderResponse(content=response.content, filetype=filetype)
