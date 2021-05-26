import io
import json
import logging
import tarfile
import tempfile
import uuid
from typing import BinaryIO, Optional

import attr
import requests
from django.conf import settings
from django.core.files import File
from tenacity import (
    before_log,
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_random_exponential,
)

from transit_odp.pipelines.exceptions import PipelineException

logger = logging.getLogger(__name__)

STATUS_SUCCESS = 0
STATUS_FAILURE = 1
STATUS_STARTING = -1


@attr.s(auto_attribs=True)
class DQSUploadUrlRes(object):
    uuid: uuid.UUID
    presigned_url: str


@attr.s(auto_attribs=True)
class DQSStatusRes(object):
    uuid: uuid.UUID
    job_exitcode: int = attr.ib(converter=int)
    job_status: str


class DQSClient(object):
    url: str
    upload_url: str
    status_url: str
    download_url: str

    def __init__(self):
        self.url = settings.DQS_URL
        self.upload_url = f"{self.url}/uploadurl"
        self.status_url = f"{self.url}/status"
        self.download_url = f"{self.url}/downloadurl"

    def upload(self, f: File) -> Optional[uuid.UUID]:
        """Upload the File `f` to DQS for processing returning the task_id UUID"""

        with tempfile.TemporaryFile(suffix=".tar.gz") as tmp:
            self._compress_file(f.open("rb"), tmp)
            tmp.seek(0)
            upload_meta = self._get_upload_url(f.name)
            self._upload_file(upload_meta.presigned_url, f=tmp)
            return upload_meta.uuid

        return None

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=4),
        stop=stop_after_attempt(3),
        before=before_log(logger, logging.DEBUG),
    )
    def get_status(self, task_id: uuid.UUID) -> DQSStatusRes:
        """Fetches the status of the processing job with task id `task_id`"""
        try:
            r = requests.get(self.status_url, params={"uuid": task_id}, timeout=60)
            r.raise_for_status()
            data = r.json()
            return DQSStatusRes(**data)
        except requests.Timeout as e:
            logger.exception(f"The request '{r.url}' timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(
                f"The request '{r.url}' returned status code {r.status_code}."
            )
            raise PipelineException from e
        except (json.decoder.JSONDecodeError, TypeError):
            logger.exception(f"The request '{r.url}' returned malformed JSON.")
            raise

    def download(self, task_id: uuid.UUID) -> bytes:
        """Download the report from DQS for job task_id UUID"""

        presigned_url = self._get_download_url(task_id)
        f_uncompressed = io.BytesIO()

        with io.BytesIO() as tmp:
            self._download_file(presigned_url, f=tmp)
            tmp.seek(0)
            self._uncompress_file(tmp, f_uncompressed)
            return f_uncompressed.getvalue()

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=4),
        stop=stop_after_attempt(5),
        before=before_log(logger, logging.DEBUG),
    )
    def _get_upload_url(self, filename: str) -> DQSUploadUrlRes:
        """Get pre-signed URL from DQS to upload dataset"""
        try:
            r = requests.get(self.upload_url, params={"filename": filename}, timeout=60)
            r.raise_for_status()
            data = r.json()
            return DQSUploadUrlRes(**data)

        except requests.Timeout as e:
            logger.exception(f"The request '{r.url}' timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(
                f"The request '{r.url}' returned status code {r.status_code}."
            )
            raise PipelineException from e
        except (json.decoder.JSONDecodeError, TypeError):
            logger.exception(f"The request '{r.url}' returned malformed JSON.")
            raise

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=4),
        stop=stop_after_attempt(5),
        before=before_log(logger, logging.DEBUG),
    )
    def _get_download_url(self, task_id: uuid.UUID) -> str:
        """Get pre-signed URL from DQS to download report"""
        try:
            r = requests.get(
                self.download_url,
                params={"uuid": task_id},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return data["presigned_url"]
        except requests.Timeout as e:
            logger.exception(f"The request '{r.url}' timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(
                f"The request '{r.url}' returned status code {r.status_code}."
            )
            raise PipelineException from e
        except (json.decoder.JSONDecodeError, KeyError):
            logger.exception(f"The request '{r.url}' returned malformed JSON.")
            raise

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_delay(300),
        before=before_log(logger, logging.DEBUG),
    )
    def _upload_file(self, upload_url: str, f: BinaryIO):
        """Uploads f to the specified upload_url

        upload_url is the dynamically generated, pre-signed url to DQS' S3 bucket
        """
        try:
            r = requests.put(upload_url, data=f, timeout=60)
            r.raise_for_status()
            return r

        except requests.Timeout as e:
            logger.exception(f"The request '{r.url}' timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(
                f"The request '{r.url}' returned status code {r.status_code}."
            )
            raise PipelineException from e

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_delay(300),  # the pre-signed url expires after 5 minutes
        before=before_log(logger, logging.DEBUG),
    )
    def _download_file(self, download_url: str, f: BinaryIO) -> bool:
        """Downloads report at `download_url` and write content to `f`

        download_url is the dynamically generated, pre-signed url to DQS' S3 bucket
        """
        try:
            r = requests.get(download_url, timeout=60)
            r.raise_for_status()
            f.write(r.content)
            return r.ok

        except requests.Timeout as e:
            logger.exception(f"The request '{r.url}' timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(
                f"The request '{r.url}' returned status code {r.status_code}."
            )
            raise PipelineException from e

    def _compress_file(self, fin: File, fout: BinaryIO) -> None:
        """Compress data in fin and write to fout as a tar.gz"""
        with tarfile.open(fileobj=fout, mode="w:gz") as tar:
            tar_info = tarfile.TarInfo(fin.name)
            # Note this line is crucial, the file will SILENTLY not be added without it
            # TODO - make independent of Django File by getting size from:
            # os.fstat(fin.fileno()).st_size
            tar_info.size = fin.size
            with fin.open("rb") as f:
                tar.addfile(tar_info, fileobj=f)

    def _uncompress_file(self, fin: BinaryIO, fout: BinaryIO) -> None:
        """Read compressed data in fin tarfile and write uncompressed to fout"""
        with tarfile.open(fileobj=fin, mode="r:gz") as tar:
            members = [member for member in tar.getmembers() if member.size > 0]
            if len(members) != 1:
                raise PipelineException("Report archive does not contain a single file")
            fout.write(tar.extractfile(members[0]).read())
