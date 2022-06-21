from collections import namedtuple
from pathlib import Path

import pytest

from transit_odp.data_quality.pti.factories import SchemaFactory
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile, XMLFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.timetables.proxies import TimetableDatasetRevision
from transit_odp.timetables.pti import PTI_PATH
from transit_odp.timetables.validate import TXCRevisionValidator

pytestmark = pytest.mark.django_db

HERE = Path(__file__)
DATA_DIR = HERE.parent / "data"

TXC = """<?xml version="1.0" encoding="UTF-8"?>
    <TransXChange xmlns="http://www.transxchange.org.uk/" xml:lang="en"
    SchemaVersion="2.4" {0}></TransXChange>
    """


@pytest.mark.parametrize(
    ("version", "modification_date", "creation_date", "expected"),
    [
        ("0", "2004-06-09T14:20:00-05:00", "2004-06-09T14:20:00-05:00", True),
        ("0", "2004-06-02T13:20:00-05:00", "2004-06-01T13:20:00-05:00", False),
        ("1", "2004-06-09T14:20:00-05:00", "2004-06-09T14:20:00-05:00", False),
        ("1", "2004-06-01T14:20:00-05:00", "2004-06-09T14:20:00-05:00", False),
        ("1", "2004-06-10T14:20:00-05:00", "2004-06-09T14:20:00-05:00", True),
    ],
)
def test_validate_modification_date_with_revision(
    version, modification_date, creation_date, expected
):
    modification_date = 'ModificationDateTime="{0}"'.format(modification_date)
    creation_date = 'CreationDateTime="{0}"'.format(creation_date)
    attributes = 'RevisionNumber="{0}" {1} {2}'
    attributes = attributes.format(version, modification_date, creation_date)
    xml = TXC.format(attributes)

    OBSERVATION_ID = 2
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = XMLFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("version", "modification", "expected"),
    [
        ("0", "new", True),
        ("1", "revise", True),
        ("10", "new", False),
        ("0", "revise", False),
        ("0", "delete", False),
        ("1", "delete", False),
    ],
)
def test_validate_modification(version, modification, expected):
    attributes = 'RevisionNumber="{0}" Modification="{1}"'
    attributes = attributes.format(version, modification)
    xml = TXC.format(attributes)

    OBSERVATION_ID = 3
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    txc = XMLFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    ("modification_datetime", "revision", "expected"),
    [
        ("2021-10-20T10:31:39", 81, 1),
        ("2021-11-21T10:34:49", 82, 0),
        ("2021-11-21T10:34:49", 81, 0),
        ("2021-11-21T10:34:49", 80, 1),
    ],
)
def test_revision_single_file_modification_changed(
    modification_datetime, revision, expected
):
    """
    GIVEN a draft revision to be validated with a change in modification datetime and
    increment in revision
    WHEN a validator is created and `get_violations` is called
    THEN no violations should be returned
    """
    live_revision = DatasetRevisionFactory()
    TXCFileAttributesFactory(
        revision=live_revision,
        modification="revise",
        revision_number="80",
        filename="X18B-None--SCWW-LS-2021-09-18-TXC LS210918-BODS_V1_1.xml",
        creation_datetime="2020-11-22T11:00:00",
        modification_datetime="2021-10-20T10:31:39",
        operating_period_start_date="2021-08-02",
        service_code="PD0000479:304",
    )

    draft = DatasetRevisionFactory(dataset=live_revision.dataset, is_published=False)
    TXCFileAttributesFactory(
        revision=draft,
        modification="revise",
        filename="X18B-None--SCWW-LS-2021-12-31-TXC LS210918-BODS_V1_1.xml",
        creation_datetime="2020-11-22T11:00:00",
        operating_period_start_date="2021-11-02",
        service_code="PD0000479:304",
        modification_datetime=modification_datetime,
        revision_number=revision,
    )
    draft = TimetableDatasetRevision.objects.get(id=draft.id)
    validator = TXCRevisionValidator(draft_revision=draft)
    violations = validator.get_violations()
    assert len(violations) == expected


def test_revision_bug_bodp_4628():
    """
    GIVEN a draft revision that contains XML files with same version header as the
    live revision.
    WHEN get_violations is called.
    THEN no violations should be generated.
    """
    live_revision = DatasetRevisionFactory()
    TXCFileAttributesFactory(
        revision=live_revision,
        modification="revise",
        revision_number="80",
        filename="X18B-None--SCWW-LS-2021-09-18-TXC LS210918-BODS_V1_1.xml",
        creation_datetime="2020-11-22T11:00:00",
        modification_datetime="2021-10-20T10:31:39",
        operating_period_start_date="2021-08-02",
        service_code="PD0000479:304",
    )
    TXCFileAttributesFactory(
        revision=live_revision,
        modification="revise",
        revision_number="84",
        filename="X18B-None--SCWW-LS-2021-10-30-TXC LS211030reg-BODS_V1_1.xml",
        creation_datetime="2020-11-22T11:00:00",
        modification_datetime="2021-10-20T10:48:17",
        operating_period_start_date="2021-10-30",
        service_code="PD0000479:304",
    )

    draft = DatasetRevisionFactory(dataset=live_revision.dataset, is_published=False)
    TXCFileAttributesFactory(
        revision=draft,
        modification="revise",
        revision_number="80",
        filename="X18B-None--SCWW-LS-2021-09-18-TXC LS210918-BODS_V1_1.xml",
        creation_datetime="2020-11-22T11:00:00",
        modification_datetime="2021-10-20T10:31:39",
        operating_period_start_date="2021-08-02",
        service_code="PD0000479:304",
    )
    TXCFileAttributesFactory(
        revision=draft,
        modification="revise",
        revision_number="84",
        filename="X18B-None--SCWW-LS-2021-10-30-TXC LS211030reg-BODS_V1_1.xml",
        creation_datetime="2020-11-22T11:00:00",
        modification_datetime="2021-10-20T10:48:17",
        operating_period_start_date="2021-10-30",
        service_code="PD0000479:304",
    )
    draft = TimetableDatasetRevision.objects.get(id=draft.id)
    validator = TXCRevisionValidator(draft_revision=draft)
    violations = validator.get_violations()
    assert len(violations) == 0


def test_revision_check_modification_doesnt_change():
    """
    GIVEN a live revision with 3 file revisions with numbers 1, 2, 3 and
    draft file revisions with numbers 4, 5, 6 and no change to the modification_datetime
    WHEN get_violations is called.
    THEN 3 violations should be generated.
    """
    FileHeader = namedtuple("FileHeader", ["revision_number", "modification_datetime"])
    live_revision = DatasetRevisionFactory()
    headers = [
        FileHeader("1", "2021-01-01T12:12:12"),
        FileHeader("2", "2021-06-01T12:12:12"),
        FileHeader("3", "2021-10-01T12:12:12"),
    ]
    for header in headers:
        TXCFileAttributesFactory(
            revision=live_revision,
            modification="revise",
            revision_number=header.revision_number,
            modification_datetime=header.modification_datetime,
            service_code="PD0000479:304",
        )

    draft_headers = [
        FileHeader("4", "2021-01-01T12:12:12"),
        FileHeader("5", "2021-06-01T12:12:12"),
        FileHeader("6", "2021-10-01T12:12:12"),
    ]
    draft = DatasetRevisionFactory(dataset=live_revision.dataset, is_published=False)
    for header in draft_headers:
        TXCFileAttributesFactory(
            revision=draft,
            modification="revise",
            service_code="PD0000479:304",
            modification_datetime=header.modification_datetime,
            revision_number=header.revision_number,
        )
    draft = TimetableDatasetRevision.objects.get(id=draft.id)
    validator = TXCRevisionValidator(draft_revision=draft)
    violations = validator.get_violations()
    assert len(violations) == len(headers)


def test_modification_datetime_change_revision_stays_the_same():
    """
    GIVEN a live revision with 3 file revisions with numbers 1, 2, 3 and
    draft file revisions with numbers 1, 2, 3 and changes to the modification_datetime
    WHEN get_violations is called.
    THEN 3 violations should be generated.
    """
    FileHeader = namedtuple("FileHeader", ["revision_number", "modification_datetime"])
    live_revision = DatasetRevisionFactory()
    headers = [
        FileHeader("1", "2021-01-01T12:12:12"),
        FileHeader("2", "2021-06-01T12:12:12"),
        FileHeader("3", "2021-10-01T12:12:12"),
    ]
    for header in headers:
        TXCFileAttributesFactory(
            revision=live_revision,
            modification="revise",
            revision_number=header.revision_number,
            modification_datetime=header.modification_datetime,
            service_code="PD0000479:304",
        )

    draft_headers = [
        FileHeader("1", "2021-01-11T12:12:12"),
        FileHeader("2", "2021-06-11T12:12:12"),
        FileHeader("3", "2021-10-11T12:12:12"),
    ]
    draft = DatasetRevisionFactory(dataset=live_revision.dataset, is_published=False)
    for header in draft_headers:
        TXCFileAttributesFactory(
            revision=draft,
            modification="revise",
            service_code="PD0000479:304",
            modification_datetime=header.modification_datetime,
            revision_number=header.revision_number,
        )
    draft = TimetableDatasetRevision.objects.get(id=draft.id)
    validator = TXCRevisionValidator(draft_revision=draft)
    violations = validator.get_violations()
    assert len(violations) == len(headers)


def test_no_violations_are_raised_when_sha1sums_match():
    """
    GIVEN a live revision
    WHEN a draft whose sha1sum match with the files in a live revision
    THEN 0 violations should be generated.
    """

    filepath = DATA_DIR / "3_pti_pass.zip"
    TxCFileAttributes = namedtuple(
        "FileHeader",
        [
            "filename",
            "service_code",
            "revision_number",
            "modification_datetime",
            "hash",
        ],
    )
    prefix = "ARBB_Z_ARBBPF0000508519Z_20220109_20220213"
    live_revision = DatasetRevisionFactory(upload_file__from_path=filepath.as_posix())
    attribs = [
        TxCFileAttributes(
            f"{prefix}_7888cd56-3ba9-45e9-9232-e71119451d73.xml",
            "PF0000508:519",
            "10",
            "2021-12-22T12:53:42",
            "e517a7eb21950ac1174a3e5f7c0bf69d26d4ba49",
        ),
        TxCFileAttributes(
            f"{prefix}_b9689420-7be3-4316-bba7-0d24351d9aaa.xml",
            "PF0000508:519",
            "10",
            "2021-12-22T12:53:41",
            "16db196c818e2d57f299b909adc6ba85010332a0",
        ),
        TxCFileAttributes(
            f"{prefix}_cc0cc896-6883-4596-8fb5-adbdf96db78f.xml",
            "PF0000508:519",
            "10",
            "2021-12-22T12:53:39",
            "885adc326683280001337cab18dcda882052fc7f",
        ),
    ]
    for attr in attribs:
        TXCFileAttributesFactory(
            filename=attr.filename,
            revision=live_revision,
            modification="revise",
            revision_number=attr.revision_number,
            modification_datetime=attr.modification_datetime,
            service_code=attr.service_code,
            hash=attr.hash,
        )

    draft = DatasetRevisionFactory(
        upload_file__from_path=filepath.as_posix(),
        dataset=live_revision.dataset,
        is_published=False,
    )
    for attr in attribs:
        TXCFileAttributesFactory(
            filename=attr.filename,
            revision=draft,
            modification="revise",
            revision_number=attr.revision_number,
            modification_datetime=attr.modification_datetime,
            service_code=attr.service_code,
            hash=attr.hash,
        )
    revision = TimetableDatasetRevision.objects.get(id=draft.id)
    validator = TXCRevisionValidator(draft_revision=revision)
    violations = validator.get_violations()
    assert len(violations) == 0
