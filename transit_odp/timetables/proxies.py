import zipfile
from typing import BinaryIO, Iterable, List

from transit_odp.common.utils import sha1sum
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.organisation.querysets import DatasetRevisionQuerySet
from transit_odp.timetables.managers import (
    TimetableDatasetManager,
    TimetableDatasetRevisionManager,
)
from transit_odp.timetables.querysets import TimetableDatasetQuerySet


class TimetableDataset(Dataset):
    class Meta:
        proxy = True

    objects = TimetableDatasetManager.from_queryset(TimetableDatasetQuerySet)()


class TimetableDatasetRevision(DatasetRevision):
    class Meta:
        proxy = True

    objects = TimetableDatasetRevisionManager.from_queryset(DatasetRevisionQuerySet)()

    def get_txc_files(self) -> Iterable[BinaryIO]:
        timetable_file = self.upload_file
        if zipfile.is_zipfile(timetable_file):
            with zipfile.ZipFile(timetable_file) as zf:
                names = [n for n in zf.namelist() if n.endswith(".xml")]
                for name in names:
                    with zf.open(name) as f:
                        yield f
        else:
            timetable_file.seek(0)
            yield timetable_file

    def get_txc_hashes(self) -> List[str]:
        return [sha1sum(file_.read()) for file_ in self.get_txc_files()]
