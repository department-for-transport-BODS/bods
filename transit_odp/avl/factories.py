import io
from zipfile import ZIP_DEFLATED, ZipFile

import factory
from factory.django import DjangoModelFactory

from transit_odp.avl.models import CAVLDataArchive, CAVLValidationTaskResult
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.factories import TaskResultFactory


def zipped_file(name, data):
    bytesio = io.BytesIO()
    with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as z:
        z.writestr(name, data)

    return bytesio


def zipped_sirivm_file():
    return zipped_file("sirivm.xml", b"<Siri>content</Siri>")


def zipped_gtfsrt_file():
    return zipped_file("gtfsrt.bin", b"content")


class CAVLValidationTaskResultFactory(TaskResultFactory):
    class Meta:
        model = CAVLValidationTaskResult

    revision = factory.SubFactory(DatasetRevisionFactory)


class CAVLDataArchiveFactory(DjangoModelFactory):
    class Meta:
        model = CAVLDataArchive

    data = factory.django.FileField(filename="sirivm.zip", from_func=zipped_sirivm_file)
    data_format = CAVLDataArchive.SIRIVM


class GTFSRTDataArchiveFactory(DjangoModelFactory):
    class Meta:
        model = CAVLDataArchive

    data = factory.django.FileField(filename="gtfsrt.zip", from_func=zipped_gtfsrt_file)
    data_format = CAVLDataArchive.GTFSRT
