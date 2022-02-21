from __future__ import annotations

import zipfile
from logging import getLogger
from pathlib import Path
from typing import BinaryIO, Iterable, List

from transit_odp.common.loggers import DatasetPipelineLoggerContext, PipelineAdapter
from transit_odp.common.types import JSONFile
from transit_odp.data_quality.pti.models import Violation
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.organisation.models import DatasetRevision

PTI_PATH = Path(__file__).parent / "pti_schema.json"

logger = getLogger(__name__)


class DatasetPTIValidator:
    def __init__(self, schema: JSONFile):
        self._validator = PTIValidator(schema)

    def iter_get_files(self, revision: DatasetRevision) -> Iterable[BinaryIO]:
        context = DatasetPipelineLoggerContext(object_id=revision.dataset_id)
        adapter = PipelineAdapter(logger, {"context": context})
        file_ = revision.upload_file
        if zipfile.is_zipfile(file_):
            with zipfile.ZipFile(file_) as zf:
                names = [n for n in zf.namelist() if n.endswith(".xml")]
                file_count = len(names)
                for index, name in enumerate(names, start=1):
                    adapter.info(
                        f"PTI Validation of file {index} of {file_count} - {name}."
                    )
                    with zf.open(name) as f:
                        yield f
        else:
            file_.seek(0)
            yield file_

    def get_violations(self, revision: DatasetRevision) -> List[Violation]:
        context = DatasetPipelineLoggerContext(object_id=revision.dataset_id)
        adapter = PipelineAdapter(logger, {"context": context})
        for xml in self.iter_get_files(revision=revision):
            self._validator.is_valid(xml)

        adapter.info(f"Revision contains {len(self._validator.violations)} violations.")
        return self._validator.violations

    @classmethod
    def from_path(cls, path: Path) -> DatasetPTIValidator:
        with path.open("r") as schema_file:
            return cls(schema_file)


def get_pti_validator() -> DatasetPTIValidator:
    """
    Gets a PTI JSON Schema and returns a DatasetPTIValidator.
    """
    with PTI_PATH.open("r") as f:
        pti = DatasetPTIValidator(f)
    return pti
