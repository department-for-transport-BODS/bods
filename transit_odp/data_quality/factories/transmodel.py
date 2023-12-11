import factory
from django.contrib.gis.geos import LineString, Point
import faker

from transit_odp.data_quality import models
from transit_odp.organisation.factories import DatasetRevisionFactory
from factory.django import DjangoModelFactory

class DataQualityReportSummaryFactory(DjangoModelFactory):
    """
    report: use absolute import path due to circular import
    see https://factoryboy.readthedocs.io/en/latest/reference.html#circular-imports
    """

    report = factory.SubFactory(
        "transit_odp.data_quality.factories.DataQualityReportFactory"
    )
    data = {}

    class Meta:
        model = models.DataQualityReportSummary


class DataQualityReportFactory(DjangoModelFactory):
    """
    summary: use this report as the report on the related summary
             subfactory on DataQualityReportSummaryFactory is skipped,
             avoiding recursion error

    file: create a DataQualityReport with a file using 'file__from_file' or
          'file__from_path',
    """

    revision = factory.SubFactory(DatasetRevisionFactory)
    summary = factory.RelatedFactory(DataQualityReportSummaryFactory, "report")
    file = factory.django.FileField(filename="report.json")
    score = 0.33

    class Meta:
        model = models.DataQualityReport


class ServiceFactory(DjangoModelFactory):
    # TODO: investigate -- threw error when trying to load TimingPatternStop
    # report = factory.SubFactory(DataQualityReportFactory)
    ito_id = factory.Sequence(lambda n: f"{n}")  # unique ito id
    name = factory.Faker("pystr_format", string_format="???:??????????")

    class Meta:
        model = models.Service


class StopPointFactory(DjangoModelFactory):
    ito_id = factory.Sequence(lambda n: f"{n}")  # unique ito id
    atco_code = factory.Sequence(lambda n: n)  # unique atco code
    name = factory.Faker("street_name")
    bearing = 1
    type = "BCT"

    @factory.lazy_attribute
    def geometry(self):
        fake=faker.Faker()
        geometry=fake.local_latlng(country_code="GB", coords_only=True)
        return Point(x=float(geometry[1]), y=float(geometry[0]), srid=4326)

    class Meta:
        model = models.StopPoint


class ServicePatternFactory(DjangoModelFactory):
    ito_id = factory.Sequence(lambda n: f"{n}")  # unique ito id
    name = ""
    service = factory.SubFactory(ServiceFactory)

    @factory.lazy_attribute
    def geometry(self):
        fake=faker.Faker()
        geometry=fake.local_latlng(country_code="GB", coords_only=True)
        return LineString(x=float(geometry[1]), y=float(geometry[0]), srid=4326)

    class Meta:
        model = models.ServicePattern

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # position sequence should start at 0 for each service pattern
        ServicePatternStopFactory.reset_sequence(0)
        return super()._create(model_class, *args, **kwargs)


class ServiceLinkFactory(DjangoModelFactory):
    ito_id = factory.Sequence(lambda n: f"{n}")  # unique ito id
    from_stop = factory.SubFactory(StopPointFactory)
    to_stop = factory.SubFactory(StopPointFactory)

    class Meta:
        model = models.ServiceLink


class ServicePatternServiceLinkFactory(DjangoModelFactory):
    service_pattern = factory.SubFactory(ServicePatternFactory)
    service_link = factory.SubFactory(ServiceLinkFactory)
    position = factory.Sequence(lambda n: str(n))

    class Meta:
        model = models.ServicePatternServiceLink


class ServicePatternStopFactory(DjangoModelFactory):
    service_pattern = factory.SubFactory(ServicePatternFactory)
    stop = factory.SubFactory(StopPointFactory)
    position = factory.Sequence(lambda n: n)

    class Meta:
        model = models.ServicePatternStop


class TimingPatternFactory(DjangoModelFactory):
    ito_id = factory.Sequence(lambda n: f"{n}")  # unique ito id
    service_pattern = factory.SubFactory(ServicePatternFactory)
    # create 5 vehicle_journeys related to this timing pattern
    vehicle_journeys = factory.RelatedFactoryList(
        "transit_odp.data_quality.factories.VehicleJourneyFactory", "timing_pattern", 5
    )

    class Meta:
        model = models.TimingPattern


class TimingPatternStopFactory(DjangoModelFactory):
    class Meta:
        model = models.TimingPatternStop
        exclude = ("common_service_pattern",)

    timing_pattern = factory.SubFactory(
        TimingPatternFactory,
        service_pattern=factory.SelfAttribute("..common_service_pattern"),
    )
    service_pattern_stop = factory.SubFactory(
        ServicePatternStopFactory,
        service_pattern=factory.SelfAttribute("..common_service_pattern"),
    )
    arrival = factory.Faker("time_delta")
    departure = factory.Faker("time_delta")

    # ensure timing_pattern and service_pattern_stop have same service_pattern
    # allow user to optionally specify that service_pattern
    # not ideal -- if want to pass timing_pattern, also have to remember to pass
    # common_service_pattern
    def common_service_pattern(
        self, create, *args, common_service_pattern=None, **kwargs
    ):
        return (
            common_service_pattern
            if common_service_pattern
            else ServicePatternFactory.create()
        )


class VehicleJourneyFactory(DjangoModelFactory):
    class Meta:
        model = models.VehicleJourney

    ito_id = factory.Sequence(lambda n: f"{n}")  # unique ito id
    timing_pattern = factory.SubFactory(TimingPatternFactory)
    start_time = factory.Faker("time_object")
    dates = factory.List(
        [factory.Faker("date_this_year", before_today=True, after_today=True)] * 4
    )  # array of 4 dates
