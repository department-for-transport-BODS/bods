from dataclasses import dataclass
from typing import List, final


@dataclass
class Properties:
    feature_name: str


@final
@dataclass
class StopProperties(Properties):
    atco_code: str
    bearing: int
    synthetic: bool
    type: str


@final
@dataclass
class ServicePatternProperties(Properties):
    length_m: float
    line: str
    route_shape: bool
    service_links: List[str]
    stops: List[str]
    timing_patterns: List[str]


@final
@dataclass
class ServiceLinkProperties(Properties):
    from_stop: str
    length_m: float
    route_shape: bool
    service_patterns: List[str]
    to_stop: str
