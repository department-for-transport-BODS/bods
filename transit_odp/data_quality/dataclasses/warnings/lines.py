from dataclasses import dataclass
from typing import List

from .base import BaseWarning


@dataclass
class LineBaseWarning(BaseWarning):
    journeys: List[str]


@dataclass
class LineExpired(LineBaseWarning):
    pass


@dataclass
class LineMissingBlockID(LineBaseWarning):
    pass
