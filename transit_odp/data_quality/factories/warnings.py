import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
)
from transit_odp.data_quality.models.warnings import (
    IncorrectNOCWarning,
)


class IncorrectNOCWarningFactory(DjangoModelFactory):
    class Meta:
        model = IncorrectNOCWarning

    noc = factory.fuzzy.FuzzyText(length=4)
    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )
