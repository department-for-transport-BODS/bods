from __future__ import annotations

import zipfile
from logging import getLogger
from pathlib import Path
from typing import BinaryIO, Iterable, List

from transit_odp.common.loggers import DatasetPipelineLoggerContext, PipelineAdapter
from transit_odp.common.types import JSONFile
from transit_odp.common.utils import sha1sum
from transit_odp.data_quality.pti.models import Violation
from transit_odp.fares_validator.views.validators import FaresValidator

FARES_SCHEMA = Path(__file__).parent.parent / "schema" / "fares_schema.json"

logger = getLogger(__name__)


class DatasetFaresValidator:
    def __init__(self, schema: JSONFile):
        self._validator = FaresValidator(schema)

    def iter_get_files(self, file, revision) -> Iterable[BinaryIO]:
        context = DatasetPipelineLoggerContext(object_id=revision)
        adapter = PipelineAdapter(logger, {"context": context})
        if zipfile.is_zipfile(file):
            with zipfile.ZipFile(file) as zf:
                names = [n for n in zf.namelist() if n.endswith(".xml")]
                file_count = len(names)
                for index, name in enumerate(names, start=1):
                    adapter.info(
                        f"Fares Validation of file {index} of {file_count} - {name}."
                    )
                    with zf.open(name) as f:
                        yield f
        else:
            file.seek(0)
            yield file

    def get_violations(self, file, revision) -> List[Violation]:
        context = DatasetPipelineLoggerContext(object_id=revision)
        adapter = PipelineAdapter(logger, {"context": context})

        for xml in self.iter_get_files(file, revision=revision):
            xml.seek(0)
            self._validator.is_valid(xml)

        adapter.info(f"Revision contains {len(self._validator.violations)} violations.")
        return self._validator.violations

    @classmethod
    def from_path(cls, path: Path) -> DatasetFaresValidator:
        with path.open("r") as schema_file:
            return cls(schema_file)


def get_fares_validator() -> DatasetFaresValidator:
    """
    Gets a FARES JSON Schema and returns a DatasetFaresValidator.
    """
    with FARES_SCHEMA.open("r") as f:
        fares_validator = DatasetFaresValidator(f)
    return fares_validator
