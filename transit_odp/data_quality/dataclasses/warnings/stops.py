from dataclasses import dataclass
from typing import List

from transit_odp.data_quality.dataclasses.warnings.base import BaseWarning


@dataclass
class StopMissingNaptan(BaseWarning):
    service_patterns: List[str]


@dataclass
class StopIncorrectType(BaseWarning):
    stop_type: str
    service_patterns: List[str]


@dataclass
class StopServiceLinkMissing(BaseWarning):
    from_stop: str
    to_stop: str
    stops: List[str]
    service_patterns: List[str]
