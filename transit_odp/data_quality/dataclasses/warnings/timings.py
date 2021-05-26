from dataclasses import dataclass
from typing import List

from transit_odp.data_quality.dataclasses.warnings.base import BaseWarning


@dataclass
class TimingBaseWarning(BaseWarning):
    none: bool
    all: bool
    indexes: List[int]


@dataclass
class TimingSpeedWarning(BaseWarning):
    indexes: List[int]
    entities: List[str]


@dataclass
class TimingSlow(TimingSpeedWarning):
    pass


@dataclass
class TimingFast(TimingSpeedWarning):
    pass


@dataclass
class TimingSpeedLinkWarning(BaseWarning):
    indexes: List[int]
    service_link: str


@dataclass
class TimingFastLink(TimingSpeedLinkWarning):
    pass


@dataclass
class TimingSlowLink(TimingSpeedLinkWarning):
    pass


@dataclass
class TimingMissingPoint(BaseWarning):
    missing_stop: str
    indexes: List[int]


@dataclass
class TimingMissingPoint15(TimingMissingPoint):
    pass


@dataclass
class TimingBackwards(TimingBaseWarning):
    pass


@dataclass
class TimingPickUp(TimingBaseWarning):
    pass


@dataclass
class TimingDropOff(TimingBaseWarning):
    pass


@dataclass
class TimingMultiple(TimingBaseWarning):
    pass


@dataclass
class TimingNone(TimingBaseWarning):
    pass


@dataclass
class TimingFirst(TimingBaseWarning):
    pass


@dataclass
class TimingLast(TimingBaseWarning):
    pass
