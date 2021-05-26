from dataclasses import dataclass
from typing import List


@dataclass
class BaseWarning:
    id: str
    warning_type: str


@dataclass
class SchemaNotTXC24(BaseWarning):
    pass


@dataclass
class IncorrectNOC(BaseWarning):
    nocs: List[str]
