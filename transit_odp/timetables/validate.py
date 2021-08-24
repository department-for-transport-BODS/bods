import zipfile
from logging import getLogger
from typing import List, Optional

from lxml import etree

from transit_odp.common.loggers import DatasetPipelineLoggerContext, PipelineAdapter
from transit_odp.data_quality.pti.models import Observation, Violation
from transit_odp.organisation.models import DatasetRevision, TXCFileAttributes
from transit_odp.validate.xml import FileValidator, XMLValidator
from transit_odp.validate.zip import ZippedValidator

from .transxchange import TXCSchemaViolation
from .utils import get_transxchange_schema

logger = getLogger(__name__)

CREATION_DATETIME_OBSERVATION = Observation(
    details=(
        "Mandatory element incorrect in 'CreationDateTime' field. The "
        "CreationDateTime should be same in all revisions for the dataset "
        "published in BODS."
    ),
    category="Versioning",
    reference="2.3",
    context="@CreationDateTime",
    number=0,
    rules=[],
)

REVISION_NUMBER_OBSERVATION = Observation(
    details=(
        "Mandatory element incorrect in 'RevisionNumber' field. The "
        "RevisionNumber value should be greater than the previous "
        "RevisionNumber for the dataset in BODS."
    ),
    category="Versioning",
    reference="2.3",
    context="@RevisionNumber",
    number=0,
    rules=[],
)


class DatasetTXCValidator:
    def __init__(self):
        self._schema = get_transxchange_schema("2.4")

    def iter_get_files(self, revision: DatasetRevision):
        context = DatasetPipelineLoggerContext(object_id=revision.dataset_id)
        adapter = PipelineAdapter(logger, {"context": context})

        file_ = revision.upload_file
        if revision.is_file_zip:
            adapter.info(f"Processing zip file {file_.name}.")
            with zipfile.ZipFile(file_) as zf:
                names = [n for n in zf.namelist() if n.endswith(".xml")]
                total_files = len(names)
                for index, name in enumerate(names, 1):
                    adapter.info(f"Validating file {index} of {total_files} - {name}.")
                    with zf.open(name) as f:
                        yield f
        else:
            adapter.info(f"Getting file 1 of 1 - {file_.name}.")
            file_.seek(0)
            yield file_

    def get_violations(self, revision: DatasetRevision):
        violations = []
        for file_ in self.iter_get_files(revision=revision):
            doc = etree.parse(file_)
            is_valid = self._schema.validate(doc)
            if not is_valid:
                for error in self._schema.error_log:
                    violations.append(TXCSchemaViolation.from_error(error))
        return violations


class TimetableFileValidator:
    def __init__(self, revision):
        self.revision = revision

    @property
    def is_zip(self):
        return self.revision.is_file_zip

    @property
    def file(self):
        self.revision.upload_file.seek(0)
        return self.revision.upload_file

    def validate(self):
        """Validates a Timetable DatasetRevision.

        Raises:
            FileTooLarge: if file size is greater than max_file_size.

            DangerousXML: if DefusedXmlException is raised during parsing.
            XMLSyntaxError: if the file cannot be parsed.

            NestedZipForbidden: if zip file contains another zip file.
            ZipTooLarge: if zip file or sum of uncompressed files are
                greater than max_file_size.
            NoDataFound: if zip file contains no files with data_file_ext extension.
        """
        FileValidator(self.file).is_too_large()
        if self.is_zip:
            with ZippedValidator(self.file) as zv:
                zv.validate()
                for name in zv.get_files():
                    with zv.open(name) as f:
                        XMLValidator(f).dangerous_xml_check()
        else:
            XMLValidator(self.file).dangerous_xml_check()


class TXCRevisionValidator:
    def __init__(self, draft_revision: DatasetRevision):
        self.revision = draft_revision
        self.dataset = draft_revision.dataset
        self.live_revision = self.dataset.live_revision
        self._live_attributes = None
        self._draft_attributes = None
        self.violations = []

    @property
    def draft_attributes(self) -> List[TXCFileAttributes]:
        """
        Returns all the TXCFileAttributes of the draft revision of this Dataset.
        """
        if self._draft_attributes is not None:
            return self._draft_attributes
        self._draft_attributes = list(self.revision.txc_file_attributes.all())
        return self._draft_attributes

    @property
    def live_attributes(self) -> List[TXCFileAttributes]:
        """
        Returns all the TXCFileAttributes of the live revision of this Dataset.
        """
        if self._live_attributes is not None:
            return self._live_attributes
        self._live_attributes = list(self.live_revision.txc_file_attributes.all())
        return self._live_attributes

    def get_live_attribute_by_service_code(
        self, code, default=None
    ) -> Optional[TXCFileAttributes]:
        """
        Returns TXCFileAttributes with source_code equal to code.
        """
        attrs = [attr for attr in self.live_attributes if attr.service_code == code]

        if len(attrs) == 0:
            return None
        elif len(attrs) == 1:
            return attrs[0]
        else:
            attrs.sort(key=lambda a: a.revision_number, reverse=True)
            return attrs[0]

    def validate_creation_datetime(self) -> None:
        """
        Validates that creation_datetime remains unchanged between revisions.
        """
        for draft in self.draft_attributes:
            live = self.get_live_attribute_by_service_code(draft.service_code)

            if live is None:
                continue

            if live.creation_datetime != draft.creation_datetime:
                self.violations.append(
                    Violation(
                        line=2,
                        filename=draft.filename,
                        name="CreationDateTime",
                        observation=CREATION_DATETIME_OBSERVATION,
                    )
                )

    def validate_revision_number(self) -> None:
        """
        Validates that revision_number increments between revisions if the
        modification_datetime has changed.
        """
        for draft in self.draft_attributes:
            live = self.get_live_attribute_by_service_code(draft.service_code)

            if live is None:
                continue

            if live.modification_datetime == draft.modification_datetime:
                continue

            if live.revision_number >= draft.revision_number:
                self.violations.append(
                    Violation(
                        line=2,
                        filename=draft.filename,
                        name="RevisionNumber",
                        observation=REVISION_NUMBER_OBSERVATION,
                    )
                )

    def get_violations(self) -> List[Violation]:
        """
        Returns any revision violations.
        """
        if self.live_revision is None:
            return self.violations

        if len(self.live_attributes) == 0:
            return self.violations

        self.validate_creation_datetime()
        self.validate_revision_number()
        return self.violations
