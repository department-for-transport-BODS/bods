from dataclasses import dataclass
from typing import List

from .properties import (
    Properties,
    ServiceLinkProperties,
    ServicePatternProperties,
    StopProperties,
)


@dataclass
class Geometry:
    coordinates: List[List]
    type: str


@dataclass
class Feature:
    geometry: Geometry
    id: str
    properties: Properties

    @classmethod
    def from_dict(cls, feature):
        Properties = cls.__dataclass_fields__["properties"].type
        properties = Properties(**feature["properties"])
        geometry = Geometry(**feature["geometry"])
        return cls(id=feature["id"], geometry=geometry, properties=properties)


@dataclass
class Stop(Feature):
    properties: StopProperties


@dataclass
class ServicePattern(Feature):
    properties: ServicePatternProperties


@dataclass
class ServiceLink(Feature):
    properties: ServiceLinkProperties


@dataclass
class Operator:
    id: str
    name: str


@dataclass
class Line:
    id: str
    name: str


@dataclass
class Timing:
    arrival_time_secs: int
    departure_time_secs: int
    pickup_allowed: bool
    setdown_allowed: bool
    timing_point: bool
    distance: int = None
    speed: int = None


@dataclass
class TimingPattern:
    id: str
    service_pattern: str
    timings: List[Timing]
    vehicle_journeys: List[str]

    @classmethod
    def from_dict(cls, timing_pattern):
        timings = [Timing(**t) for t in timing_pattern["timings"]]
        return cls(
            id=timing_pattern["id"],
            service_pattern=timing_pattern["service_pattern"],
            timings=timings,
            vehicle_journeys=timing_pattern["vehicle_journeys"],
        )


@dataclass
class VehicleJourney:
    id: str
    timing_pattern: str
    start: int
    feature_name: str
    headsign: str
    dates: List[str]
