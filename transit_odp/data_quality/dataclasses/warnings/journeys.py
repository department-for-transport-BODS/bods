from dataclasses import dataclass
from typing import List

from transit_odp.data_quality.dataclasses.warnings.base import BaseWarning


@dataclass
class JourneyInappropriateStop(BaseWarning):
    stop_type: str
    vehicle_journeys: List[str]


@dataclass
class JourneyStopVariant(BaseWarning):
    vehicle_journeys: List[str]


@dataclass
class JourneysWithoutHeadsign(BaseWarning):
    pass


@dataclass
class JourneyBackwardsDateRange(BaseWarning):
    start: str
    end: str


@dataclass
class JourneyDuplicate(BaseWarning):
    duplicate: str


@dataclass
class JourneyConflict(BaseWarning):
    conflict: str
    stops: List[str]


@dataclass
class JourneyPartialTimingOverlap(BaseWarning):
    conflict: str
    stops: List[str]
