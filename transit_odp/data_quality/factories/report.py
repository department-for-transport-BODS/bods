import io
from zipfile import ZIP_DEFLATED, ZipFile

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from transit_odp.data_quality.models.report import PTIObservation, PTIValidationResult
from transit_odp.organisation.factories import DatasetRevisionFactory


def generate_blank_report():
    content = (
        "Filename,XML Line Number,XML Element,Category,Details,Reference,Important Note"
    )
    bytesio = io.BytesIO()
    with ZipFile(bytesio, mode="w", compression=ZIP_DEFLATED) as z:
        z.writestr("pti_observations.csv", content)

    return bytesio


class PTIObservationFactory(DjangoModelFactory):
    class Meta:
        model = PTIObservation

    revision = factory.SubFactory(DatasetRevisionFactory)
    filename = "file.xml"
    line = 1
    details = "This should not be happening."
    element = "Element"
    category = "Accessibility Information"
    reference = "2.4.3"
    created = factory.LazyFunction(timezone.now)


class PTIValidationResultFactory(DjangoModelFactory):
    class Meta:
        model = PTIValidationResult

    revision = factory.SubFactory(DatasetRevisionFactory)
    count = 2
    created = factory.LazyFunction(timezone.now)
    report = factory.django.FileField(
        filename="pti_validation_revision.zip", from_func=generate_blank_report
    )
