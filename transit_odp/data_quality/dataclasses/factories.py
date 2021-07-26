import random
import string

import factory
from factory import Factory, SubFactory
from faker import Faker

from transit_odp.data_quality.dataclasses.features import (
    Geometry,
    Line,
    ServiceLink,
    ServicePattern,
    Stop,
    Timing,
    TimingPattern,
    VehicleJourney,
)
from transit_odp.data_quality.dataclasses.properties import (
    ServiceLinkProperties,
    ServicePatternProperties,
    StopProperties,
)

fake = Faker()


def generate_points(num_of_points=1):
    points = []
    for _ in range(num_of_points):
        point = [float(p) for p in fake.latlng()]
        points.append(point)

    return points


class PointGeometryFactory(Factory):
    class Meta:
        model = Geometry

    coordinates = generate_points(num_of_points=1)
    type = "Point"


class LineStringGeometryFactory(Factory):
    class Meta:
        model = Geometry

    coordinates = generate_points(num_of_points=2)
    type = "LineString"


class LineFactory(Factory):
    class Meta:
        model = Line

    id = factory.Sequence(lambda n: fake.numerify("LI#######") + f"{n}")
    name = fake.street_name()


class StopPropertiesFactory(Factory):
    class Meta:
        model = StopProperties

    feature_name = fake.street_name()
    bearing = fake.random_element([0, 1])
    synthetic = fake.random_element([True, False])
    type = fake.lexify("???", letters=string.ascii_uppercase)

    @factory.sequence
    def atco_code(n):
        return fake.numerify("#########") + f"{n}"


class StopFactory(Factory):
    class Meta:
        model = Stop

    id = factory.Sequence(lambda n: fake.numerify("ST#######") + f"{n}")
    geometry = SubFactory(PointGeometryFactory)
    properties = SubFactory(StopPropertiesFactory)


class ServiceLinkPropertiesFactory(Factory):
    class Meta:
        model = ServiceLinkProperties

    feature_name = fake.street_name()
    route_shape = False
    service_patterns = ["SP1", "SP2"]
    length_m = random.uniform(250.0, 350.0)

    @factory.sequence
    def from_stop(n):
        return fake.numerify("ST1####") + f"{n}"

    @factory.sequence
    def to_stop(n):
        return fake.numerify("ST2####") + f"{n}"


class ServiceLinkFactory(Factory):
    class Meta:
        model = ServiceLink

    id = factory.Sequence(lambda n: fake.numerify("SL#######") + f"{n}")
    geometry = SubFactory(LineStringGeometryFactory)
    properties = SubFactory(ServiceLinkPropertiesFactory)


class ServicePatternPropertiesFactory(Factory):
    class Meta:
        model = ServicePatternProperties

    feature_name = fake.street_name()
    length_m = random.uniform(250.0, 350.0)
    line = fake.numerify("LI#####")
    route_shape = True
    service_links = []
    stops = []
    timing_patterns = []


class ServicePatternFactory(Factory):
    class Meta:
        model = ServicePattern

    id = factory.Sequence(lambda n: fake.numerify("SP#######") + f"{n}")
    geometry = SubFactory(LineStringGeometryFactory)
    properties = SubFactory(ServicePatternPropertiesFactory)


class TimingPatternFactory(Factory):
    class Meta:
        model = TimingPattern

    id = factory.Sequence(lambda n: fake.numerify("TP#######") + f"{n}")
    service_pattern = fake.numerify("SP#####")
    timings = []
    vehicle_journeys = []


class TimingFactory(Factory):
    class Meta:
        model = Timing

    arrival_time_secs = 0
    departure_time_secs = 0
    pickup_allowed = True
    setdown_allowed = False
    timing_point = True
    distance = None
    speed = None


class VehicleJourneyFactory(Factory):
    class Meta:
        model = VehicleJourney

    @factory.lazy_attribute
    def dates(self):
        dates = []
        for _ in range(5):
            dates.append(fake.date())

        return dates

    id = factory.Sequence(lambda n: fake.numerify("VJ#######") + f"{n}")
    timing_pattern = fake.numerify("TP#####")
    start = fake.random_int()
    feature_name = fake.street_name()
    headsign = fake.street_name() + " to " + fake.street_name()
