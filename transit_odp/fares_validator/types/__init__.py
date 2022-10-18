import json
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel


class Rule(BaseModel):
    test: str


class Observation(BaseModel):
    details: str
    category: str
    reference: str
    context: str
    number: int
    rules: List[Rule]


class Header(BaseModel):
    namespaces: Dict[str, str]


class Schema(BaseModel):
    observations: List[Observation]
    header: Header

    @classmethod
    def from_path(cls, path: Path):
        with path.open("r") as f:
            d = json.load(f)
            return cls(**d)


class Violation(BaseModel):
    line: int
    filename: str
    name: str
    element_text: Optional[str] = None
    observation: Observation
