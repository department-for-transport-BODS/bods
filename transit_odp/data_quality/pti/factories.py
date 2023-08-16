from factory import Factory, SubFactory

from transit_odp.data_quality.pti.models import (
    Header,
    Observation,
    Rule,
    Schema,
    Violation,
)


class RuleFactory(Factory):
    class Meta:
        model = Rule

    test = ""


class HeaderFactory(Factory):
    class Meta:
        model = Header

    namespaces = {"x": "http://www.transxchange.org.uk/"}
    version = "1.0.0"
    guidance_document = (
        "https://pti.org.uk/system/files/files/"
        "TransXChange%20UK%20PTI%20Profile%20v1.1.pdf"
    )
    notes = ""


class ObservationFactory(Factory):
    class Meta:
        model = Observation

    category = "Accessibility Information"
    condition = ""
    details = "This should be happening."
    reference = "2.4.3"
    context = "//x:PassengerInfo"
    number = 1
    rules = []


class SchemaFactory(Factory):
    class Meta:
        model = Schema

    header = SubFactory(HeaderFactory)
    observations = []


class ViolationFactory(Factory):
    class Meta:
        model = Violation

    line = 1
    filename = "file.xml"
    name = "Element"
    observation = SubFactory(ObservationFactory)
