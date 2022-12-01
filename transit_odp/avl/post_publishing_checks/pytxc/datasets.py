import io
import zipfile
from collections import OrderedDict
from pathlib import Path
from typing import IO, List, Optional

import requests
from requests import RequestException

from .timetables import Timetable

BODS_URL = "https://data.bus-data.dft.gov.uk"
DATASET_DOWNLOAD_URL = BODS_URL + "/timetable/dataset/{id}/download"


class ParseException(Exception):
    pass


class Dataset:
    def __init__(self, timetables: List[Timetable]):
        self.timetables = OrderedDict(
            {timetable.header.file_name: timetable for timetable in timetables}
        )

    def __len__(self) -> int:
        return len(self.timetables.keys())

    def __getitem__(self, item) -> Timetable:
        return list(self.timetables.values())[item]

    def get_timetable_by_name(self, name: str) -> Optional[Timetable]:
        return self.timetables.get(name, None)

    @classmethod
    def from_zip_file(cls, file: IO[bytes]) -> "Dataset":
        timetables = []
        with zipfile.ZipFile(file) as zf:
            filenames = zf.namelist()
            for filename in filenames:
                with zf.open(filename) as f:
                    timetables.append(Timetable.from_file(f))
        return cls(timetables)

    @classmethod
    def from_bods_url(cls, url: str) -> "Dataset":
        try:
            response = requests.get(url, timeout=15)
        except RequestException:
            raise ParseException(f"Unable to retrieve data set from {url}")
        else:
            if response.headers.get("Content-Type") == "application/zip":
                bytes_ = io.BytesIO(response.content)
                return cls.from_zip_file(bytes_)
            # Single XML file
            bytes_ = io.BytesIO(response.content)
            return cls([Timetable.from_file(bytes_)])

    @classmethod
    def from_bods_id(cls, id: int) -> "Dataset":
        url = DATASET_DOWNLOAD_URL.format(id=id)
        return cls.from_bods_url(url)

    @classmethod
    def from_zip_path(cls, path: Path) -> "Dataset":
        with path.open("rb") as f:
            return cls.from_zip_file(f)

    @classmethod
    def from_zip_path_str(cls, path: str) -> "Dataset":
        return cls.from_zip_path(Path(path))
