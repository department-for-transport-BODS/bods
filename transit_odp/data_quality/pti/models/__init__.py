import json
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

from transit_odp.data_quality.pti.constants import (
    NO_REF,
    REF_PREFIX,
    REF_SUFFIX,
    REF_URL,
    get_important_note,
)

GENERAL_REF = NO_REF + REF_URL


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
    version: str
    notes: str
    guidance_document: str


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

    def to_bods_csv(self):
        if self.observation.reference != "0":
            ref = REF_PREFIX + self.observation.reference + REF_SUFFIX + REF_URL
        else:
            ref = GENERAL_REF

        return [
            self.filename,
            self.line,
            self.name,
            self.observation.category,
            self.observation.details.format(element_text=self.element_text),
            ref,
            get_important_note(),
        ]
