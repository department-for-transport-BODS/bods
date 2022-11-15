import io
from datetime import date, datetime
from zipfile import ZIP_DEFLATED, ZipFile

import factory
from factory.django import DjangoModelFactory

from transit_odp.avl.models import (
    AVLSchemaValidationReport,
    AVLValidationReport,
    CAVLDataArchive,
    CAVLValidationTaskResult,
    PostPublishingCheckReport,
    PPCReportType,
)
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetRevisionFactory,
)
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


def zipped_csv_file():
    return zipped_file("avl_report.csv", b"operatorRef,vehicleRef")


class AVLValidationReportFactory(DjangoModelFactory):
    revision = factory.SubFactory(AVLDatasetRevisionFactory)
    critical_count = 1
    non_critical_count = 1
    critical_score = 0.7
    non_critical_score = 0.7
    vehicle_activity_count = 2
    file = factory.django.FileField(
        filename="avl_report.csv", from_func=zipped_csv_file
    )
    created = datetime.now().date()

    class Meta:
        model = AVLValidationReport


class AVLSchemaValidationReportFactory(DjangoModelFactory):
    revision = factory.SubFactory(AVLDatasetRevisionFactory)
    error_count = 1
    file = factory.django.FileField(
        filename="avl_report.csv", from_func=zipped_csv_file
    )
    created = datetime.now().date()

    class Meta:
        model = AVLSchemaValidationReport


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


class PostPublishingCheckReportFactory(DjangoModelFactory):
    class Meta:
        model = PostPublishingCheckReport

    file = factory.django.FileField(filename="dummy_file.json")
    dataset = factory.SubFactory(DatasetFactory)
    granularity = PPCReportType.DAILY
    created = date.today()


class PPCReportFactory(DjangoModelFactory):
    class Meta:
        model = PostPublishingCheckReport

    dataset = factory.SubFactory(DatasetFactory)
    created = date.today()
    granularity = PPCReportType.DAILY
    file = factory.django.FileField(filename="dummy_report.json")
