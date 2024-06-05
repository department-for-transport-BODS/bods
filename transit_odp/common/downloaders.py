from io import BytesIO

from botocore.exceptions import ClientError


class GTFSDownloadError(Exception):
    pass


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        start = len(prefix)
        return text[start:]
    return text


def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return text


class GTFSFile:
    prefix = "itm_"
    suffix = "_gtfs.zip"

    def __init__(self, filename: str, file: BytesIO = None):
        self.filename = filename
        self.file = file

    @property
    def pretty_name(self):
        return " ".join([part for part in self.id.split("_")]).title()

    @property
    def id(self):
        id_ = remove_prefix(self.filename, self.prefix)
        id_ = remove_suffix(id_, self.suffix)
        return id_

    @classmethod
    def from_id(cls, id_):
        return cls(cls.prefix + id_ + cls.suffix)


class GTFSFileDownloader:
    def __init__(self, service):
        if callable(service):
            self._service = service()
        elif service:
            self._service = service

    def download_file(self, filename):
        try:
            file_ = self._service.get_file(filename)
        except ClientError:
            return GTFSFile(filename=filename)

        file_.seek(0)
        return GTFSFile(filename=filename, file=file_)

    def download_file_by_id(self, id_):
        gtfs = GTFSFile.from_id(id_)
        return self.download_file(gtfs.filename)

    def get_files(self):
        filenames = self._service.get_file_names()
        return [GTFSFile(filename) for filename in filenames]
