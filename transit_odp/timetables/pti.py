import zipfile
from pathlib import Path

from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.organisation.models import DatasetRevision


class DatasetPTIValidator:
    def __init__(self, schema):
        self._validator = PTIValidator(schema)

    def iter_get_files(self, revision: DatasetRevision):
        file_ = revision.upload_file
        if zipfile.is_zipfile(file_):
            with zipfile.ZipFile(file_) as zf:
                names = [n for n in zf.namelist() if n.endswith(".xml")]
                for name in names:
                    with zf.open(name) as f:
                        yield f
        else:
            file_.seek(0)
            yield file_

    def get_violations(self, revision: DatasetRevision):
        for f in self.iter_get_files(revision=revision):
            self._validator.is_valid(f)

        return self._validator.violations

    @classmethod
    def from_path(cls, path: Path):
        with path.open("r") as f:
            return cls(f)
