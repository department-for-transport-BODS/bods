from unittest.mock import patch

import pytest
import requests
from requests import Response

from transit_odp.validate.downloader import (
    DataDownloader,
    DownloaderResponse,
    DownloadException,
    DownloadTimeout,
    PermissionDenied,
    UnknownFileType,
)


@pytest.mark.parametrize(
    "status_code,exception",
    [(401, PermissionDenied), (403, PermissionDenied), (402, DownloadException)],
)
def test_raise_for_status(status_code, exception, mocker):
    url = "http://fakeurl.com"
    response = mocker.Mock(spec=Response, status_code=status_code)
    downloader = DataDownloader(url)
    with pytest.raises(exception):
        downloader.raise_for_status(response)


def test_make_request(mocker):
    url = "http://fakeurl.com"
    response = mocker.Mock(spec=Response, status_code=200)
    mrequest = mocker.patch(
        "transit_odp.validate.downloader.requests.request", return_value=response
    )
    downloader = DataDownloader(url)
    downloader._make_request("GET")
    mrequest.assert_called_with("GET", url, auth=None, timeout=30)


@pytest.mark.parametrize(
    "side_effect,exception",
    [
        (requests.Timeout, DownloadTimeout),
        (requests.RequestException, DownloadException),
    ],
)
def test_make_request_exceptions(side_effect, exception, mocker):
    url = "http://fakeurl.com"
    request = "transit_odp.validate.downloader.requests.request"
    mocker.patch(request, side_effect=side_effect)
    downloader = DataDownloader(url)
    with pytest.raises(exception):
        downloader._make_request("GET")


def test_downloader_get_unknown_file_type(mocker):
    url = "http://fakeurl.com"
    response = mocker.Mock(spec=Response, content=b"", status_code=200, headers={})
    with patch.object(DataDownloader, "_make_request") as make_request:
        make_request.return_value = response
        downloader = DataDownloader(url)
        with pytest.raises(UnknownFileType):
            downloader.get()


def test_downloader_get_downloader_response(mocker):
    url = "http://fakeurl.com"
    content = b"<Root><Child>hello,world</Child></Root>"
    headers = {"Content-Type": "text/xml"}
    response = mocker.Mock(
        spec=Response,
        content=content,
        status_code=200,
        headers=headers,
    )
    with patch.object(DataDownloader, "_make_request") as make_request:
        make_request.return_value = response
        downloader = DataDownloader(url)
        actual = downloader.get()
        expected = DownloaderResponse(content=content, filetype="xml")
        assert expected == actual
