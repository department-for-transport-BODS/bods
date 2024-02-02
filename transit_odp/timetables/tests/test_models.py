import pytest

from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.timetables.dataclasses.factories import TXCFileFactory

pytestmark = pytest.mark.django_db


def test_txc_file_attributes_from_txc_file():
    revision = DatasetRevisionFactory()
    file_ = TXCFileFactory()
    attr = TXCFileAttributes.from_txc_file(file_, revision.id)
    attr.save()

    attrs = TXCFileAttributes.objects.filter(revision_id=revision.id)
    assert attrs.count() == 1
    attr = attrs.first()
    assert attr.creation_datetime == file_.header.creation_datetime
    assert attr.modification_datetime == file_.header.modification_datetime
    assert attr.service_code == file_.service_code
    assert attr.modification == file_.header.modification
    assert attr.revision_number == file_.header.revision_number
    assert attr.schema_version == file_.header.schema_version
