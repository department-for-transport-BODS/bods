from django_extensions.db.fields import CreationDateTimeField

import factory
import faker

from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.factories import (
    OrganisationFactory,
    DatasetRevisionFactory,
)
from factory.django import DjangoModelFactory

FAKER = faker.Faker()


class FaresValidationResultFactory(DjangoModelFactory):
    class Meta:
        model = FaresValidationResult

    revision = factory.SubFactory(DatasetRevisionFactory)
    organisation = factory.SubFactory(OrganisationFactory)
    count = "2"
    report_file_name = FAKER.file_name(extension="xml")
    created = CreationDateTimeField()
