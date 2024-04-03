import io
import json
import logging
import tarfile
import tempfile
import uuid
from typing import BinaryIO, Optional

import requests
from django.conf import settings
from django.core.files import File
from pydantic import BaseModel
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


class DQSUploadUrlRes(BaseModel):
    uuid: uuid.UUID
    presigned_url: str


class DQSStatusRes(BaseModel):
    uuid: uuid.UUID
    job_exitcode: int
    job_status: str


class DQSClient:
    def __init__(self):
        self.url = settings.DQS_URL

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
        url = f"{self.url}/status"
        try:
            logger.info(f"The request url for {task_id} is {url}")
            response = requests.get(url, params={"uuid": task_id}, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as e:
            logger.exception(f"The request {url} timed out for {task_id}.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(
                f"Request to {url!r} resulted in HTTPError for {task_id}.", exc_info=e
            )
            raise PipelineException from e
        except (json.decoder.JSONDecodeError, TypeError) as e:
            logger.exception(
                f"The request {url!r} returned malformed JSON for {task_id}."
            )
            raise PipelineException from e
        except Exception as e:
            logger.exception(
                f"Unexpected exception occurred in DQS monitor pipeline when running for {task_id} :: {e}"
            )
            raise PipelineException from e
        else:
            logger.info(f"DQSStatusRes data for {task_id} is :: {data}")
            return DQSStatusRes(**data)

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

        url = f"{self.url}/uploadurl"
        try:
            r = requests.get(url, params={"filename": filename}, timeout=60)
            r.raise_for_status()
            data = r.json()
        except requests.Timeout as exc_info:
            logger.exception(f"The request {url!r} timed out.", exc_info=exc_info)
            raise PipelineException from exc_info
        except requests.exceptions.HTTPError as exc_info:
            logger.exception(f"Request {url!r} returned HTTPError.", exc_info=exc_info)
            raise PipelineException from exc_info
        except (json.decoder.JSONDecodeError, TypeError) as exc_info:
            logger.exception(f"The request {url!r} returned malformed JSON.")
            raise PipelineException from exc_info
        else:
            return DQSUploadUrlRes(**data)

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=4),
        stop=stop_after_attempt(5),
        before=before_log(logger, logging.DEBUG),
    )
    def _get_download_url(self, task_id: uuid.UUID) -> str:
        """Get pre-signed URL from DQS to download report"""
        url = f"{self.url}/downloadurl"
        params = {"uuid": task_id}
        try:
            r = requests.get(
                url,
                params=params,
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return data["presigned_url"]
        except requests.Timeout as e:
            logger.exception(f"The request {url!r} timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(f"Request to {url!r} resulted in a HTTPError.")
            raise PipelineException from e
        except (json.decoder.JSONDecodeError, KeyError) as e:
            logger.exception(f"The request {url!r} returned malformed JSON.")
            raise PipelineException from e

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_delay(300),
        before=before_log(logger, logging.DEBUG),
    )
    def _upload_file(self, url: str, f: BinaryIO):
        """Uploads f to the specified upload_url

        url is the dynamically generated, pre-signed url to DQS' S3 bucket
        """
        try:
            response = requests.put(url, data=f, timeout=60)
            response.raise_for_status()
        except requests.Timeout as e:
            logger.exception(f"The request {url!r} timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(f"Request to {url!r} returned HTTPError.")
            raise PipelineException from e
        else:
            return response

    @retry(
        reraise=True,
        wait=wait_random_exponential(multiplier=1, max=60),
        stop=stop_after_delay(300),  # the pre-signed url expires after 5 minutes
        before=before_log(logger, logging.DEBUG),
    )
    def _download_file(self, url: str, f: BinaryIO) -> bool:
        """Downloads report at `url` and write content to `f`

        url is the dynamically generated, pre-signed url to DQS' S3 bucket
        """
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            f.write(response.content)
            return response.ok

        except requests.Timeout as e:
            logger.exception(f"The request {url!r} timed out.")
            raise PipelineException from e
        except requests.exceptions.HTTPError as e:
            logger.exception(f"The request {url!r} returned status code.")
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
