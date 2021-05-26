import io
import tarfile
import uuid

import pytest
from django.core.files.base import ContentFile

from transit_odp.data_quality.dqs.client import DQSClient, DQSStatusRes, DQSUploadUrlRes

MUT = "transit_odp.data_quality.dqs.client"


@pytest.fixture()
def dqs_client(settings):
    # Create DQSClient
    settings.DQS_URL = "http://www.example.com"
    return DQSClient()


class TestDQSClientAPI:
    """Test public API of DQSClient"""

    def test_upload(self, dqs_client, mocker):
        expected_task_id = uuid.uuid4()

        # Create Django File object
        f = ContentFile(b"these are bytes", name="dataset.xml")

        # Mock out TemporaryFile
        tmp_file = mocker.Mock()
        mocked_TemporaryFile = mocker.patch(f"{MUT}.tempfile.TemporaryFile")
        mocked_TemporaryFile.return_value.__enter__.return_value = tmp_file

        # Mock out _compress_file
        def side_effect(fin, fout):
            fout.compressed = True
            fout.data = fin.read()

        mocker.patch.object(dqs_client, "_compress_file", side_effect=side_effect)

        # Mock out get_upload_url
        mocker.patch.object(
            dqs_client,
            "_get_upload_url",
            return_value=DQSUploadUrlRes(
                presigned_url="www.s3bucket.com", uuid=expected_task_id
            ),
        )

        # Mock out _upload_file
        mocked_upload = mocker.patch.object(
            dqs_client,
            "_upload_file",
            return_value=True,
        )

        # Test
        task_id = dqs_client.upload(f)

        # Assert
        assert task_id == expected_task_id

        # a temporary file is created
        mocked_TemporaryFile.assert_called_once_with(suffix=".tar.gz")

        # tmp_file was compressed and received data from f
        assert tmp_file.compressed
        assert tmp_file.data == b"these are bytes"

        mocked_upload.assert_called_once_with("www.s3bucket.com", f=tmp_file)

    def test_get_status(self, dqs_client, mocker):
        task_id = uuid.uuid4()

        # Mock out requests/response
        mocked_res = mocker.Mock()
        mocked_res.raise_for_status.return_value = None
        mocked_res.json.return_value = {
            "uuid": task_id,
            "job_status": "job started",
            "job_exitcode": "-1",
        }

        mocked_get = mocker.patch(f"{MUT}.requests.get", return_value=mocked_res)

        # Test
        data = dqs_client.get_status(task_id=task_id)

        # Assert
        mocked_get.assert_called_once_with(
            dqs_client.status_url, params={"uuid": task_id}, timeout=60
        )

        assert isinstance(data, DQSStatusRes)
        assert data.uuid == task_id
        assert data.job_status == "job started"
        assert data.job_exitcode == -1

    def test_download(self, dqs_client, mocker):
        task_id = uuid.uuid4()

        mocker.patch.object(
            dqs_client, "_get_download_url", return_value="www.s3bucket.com"
        )

        def _download_file_side_effect(url, f):
            f.write(b"Hello")
            f.seek(0)

        mocker.patch.object(
            dqs_client, "_download_file", side_effect=_download_file_side_effect
        )

        def _download_file_uncompress_file(fin, fout):
            fout.write(fin.read() + b" World")
            fout.seek(0)

        mocker.patch.object(
            dqs_client, "_uncompress_file", side_effect=_download_file_uncompress_file
        )

        # Test
        data = dqs_client.download(task_id)

        # Assert
        assert data == b"Hello World"


class TestDQSClient:
    """Test internal methods on DQSClient"""

    def test_compress_file(self, dqs_client, tmp_path):
        # Create Django File object
        f = ContentFile(b"these are bytes", name="dataset.xml")

        # get temporary outpath
        outpath = tmp_path / "dataset.tar.gz"

        # Test
        with open(outpath, "wb") as fout:
            dqs_client._compress_file(f, fout)

        # Assert
        # outpath is a tar file
        assert tarfile.is_tarfile(outpath)

        # outpath is also gzipped (implied if opens successfully)
        with tarfile.open(outpath, "r:gz") as tar:
            # tar contains member name 'dataset.xml'
            assert "dataset.xml" in tar.getnames()

            with tar.extractfile("dataset.xml") as fin:
                # member 'dataset.xml' contains the same data as f
                assert fin.read() == b"these are bytes"

    def test_uncompress_file(self, dqs_client, tmp_path):
        # Create file streams
        f_archive = io.BytesIO()
        f_extract = io.BytesIO()

        # Write tar.gz data to f_archive
        with tarfile.open(mode="w:gz", fileobj=f_archive) as tar:
            data = b"test xml data"
            tar_info = tarfile.TarInfo("dataset.xml")
            tar_info.size = len(data)
            tar.addfile(tar_info, fileobj=io.BytesIO(data))

        f_archive.seek(0)

        # Test
        dqs_client._uncompress_file(f_archive, f_extract)

        # Assert
        f_extract.seek(0)
        assert f_extract.read() == b"test xml data"

    def test_get_upload_url(self, dqs_client, mocker):
        task_id = uuid.uuid4()
        presigned_url = "www.s3bucket.com"

        # Mock out requests/response
        mocked_res = mocker.Mock()
        mocked_res.ok = True
        mocked_res.json.return_value = {
            "uuid": task_id,
            "presigned_url": presigned_url,
        }

        mocked_get = mocker.patch(f"{MUT}.requests.get", return_value=mocked_res)

        # Test
        data = dqs_client._get_upload_url(filename="testdata.tar.gz")

        # Assert
        mocked_get.assert_called_once_with(
            dqs_client.upload_url, params={"filename": "testdata.tar.gz"}, timeout=60
        )

        assert isinstance(data, DQSUploadUrlRes)
        assert data.presigned_url == presigned_url
        assert data.uuid == task_id

    def test_upload_file(self, dqs_client, mocker):
        data = io.BytesIO(b"these are bytes")
        upload_url = "www.s3bucket.com"

        # Mock out requests/response
        mocked_res = mocker.Mock()
        mocked_res.ok = True

        mocked_put = mocker.patch(f"{MUT}.requests.put", return_value=mocked_res)

        # Test
        r = dqs_client._upload_file(upload_url, f=data)

        # Assert
        mocked_put.assert_called_once_with(upload_url, data=data, timeout=60)

        assert r is mocked_res

    def test_get_download_url(self, dqs_client, mocker):
        task_id = uuid.uuid4()
        presigned_url = "www.s3bucket.com"

        mocked_res = mocker.Mock()
        mocked_res.raise_for_status.return_value = None
        mocked_res.json.return_value = {
            "uuid": task_id,
            "presigned_url": presigned_url,
        }

        mocked_get = mocker.patch(f"{MUT}.requests.get", return_value=mocked_res)

        result = dqs_client._get_download_url(task_id=task_id)

        mocked_get.assert_called_once_with(
            dqs_client.download_url,
            params={"uuid": task_id},
            timeout=60,
        )

        assert result == presigned_url
