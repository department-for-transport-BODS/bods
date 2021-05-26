import io
from logging import getLogger
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from django.core.files import File
from django.utils import timezone
from requests import RequestException

from transit_odp.avl.models import CAVLDataArchive

logger = getLogger(__name__)


class ArchivingError(Exception):
    pass


class ConsumerAPIArchiver:
    data_format = CAVLDataArchive.SIRIVM
    extension = ".xml"

    def __init__(self, url):
        self.url = url
        self._archive = self.get_object()
        self._access_time = None
        self._content = None

    @property
    def filename(self):
        now = self.access_time.strftime("%Y-%m-%d_%H%M%S")
        return self.data_format_value + "_" + now + ".zip"

    @property
    def data_format_value(self):
        return self._archive.get_data_format_display().lower().replace(" ", "")

    @property
    def access_time(self):
        if self._content is None:
            raise ValueError("`content` has not been fetched yet.")

        if self._access_time is None:
            raise ValueError("`access_time` has not been set.")

        return self._access_time

    @property
    def content(self):
        if self._content is None:
            self._content = self._get_content()
        return self._content

    @property
    def content_filename(self):
        return self.data_format_value + self.extension

    def archive(self):
        file_ = self.get_file(self.content)
        self.save_to_database(file_)

    def _get_content(self):
        try:
            response = requests.get(self.url)
        except RequestException:
            msg = f"Unable to retrieve data from {self.url}"
            logger.error(msg)
            raise ArchivingError(msg)
        else:
            self._access_time = timezone.now()
            return response.content

    def get_file(self, content):
        bytesio = io.BytesIO()
        with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.writestr(self.content_filename, content)
        return bytesio

    def get_object(self):
        archive = CAVLDataArchive.objects.filter(data_format=self.data_format).last()
        if archive is None:
            archive = CAVLDataArchive(data_format=self.data_format)
        return archive

    def save_to_database(self, bytesio):
        file_ = File(bytesio, name=self.filename)
        self._archive.data = file_
        self._archive.save()


class SiriVMArchiver(ConsumerAPIArchiver):
    data_format = CAVLDataArchive.SIRIVM
    extension = ".xml"


class GTFSRTArchiver(ConsumerAPIArchiver):
    data_format = CAVLDataArchive.GTFSRT
    extension = ".bin"
