import json
from dataclasses import dataclass
from typing import Dict, List, Union, final

from .features import (
    Line,
    Operator,
    ServiceLink,
    ServicePattern,
    Stop,
    TimingPattern,
    VehicleJourney,
)
from .warnings import BaseWarning, factory

StrOrList = Union[str, List[str]]


@final
class Model:
    def __init__(self, model: Dict):
        self._model = model

    @classmethod
    def from_file(cls, source):
        if hasattr(source, "read"):
            model = json.load(source)["model"]
        else:
            with open(source, "r") as f:
                model = json.load(f)["model"]
        return cls(model)

    def _get_features(self, type_):
        return self._model.get(type_, {}).get("features")

    @property
    def stop_ids(self) -> List[str]:
        return [s.id for s in self.stops]

    @property
    def stops(self) -> List[Stop]:
        features = self._get_features("stops")
        return [Stop.from_dict(d) for d in features]

    @property
    def service_patterns(self) -> List[ServicePattern]:
        features = self._get_features("service_patterns")
        return [ServicePattern.from_dict(d) for d in features]

    @property
    def service_links(self) -> List[ServiceLink]:
        features = self._get_features("service_links")
        return [ServiceLink.from_dict(d) for d in features]

    @property
    def lines(self) -> List[Line]:
        return [Line(**t) for t in self._model.get("lines", [])]

    @property
    def timing_patterns(self) -> List[TimingPattern]:
        return [
            TimingPattern.from_dict(t) for t in self._model.get("timing_patterns", [])
        ]

    @property
    def vehicle_journeys(self) -> List[VehicleJourney]:
        return [VehicleJourney(**t) for t in self._model.get("vehicle_journeys", [])]

    @property
    def operators(self) -> List[Operator]:
        return [Operator(**o) for o in self._model.get("operators", [])]

    def get_timing_pattern_by_id(self, id_):
        return [tp for tp in self.timing_patterns if tp.id == id_][0]


@dataclass
class Schema:
    url: str
    version: str


@dataclass
class Header:
    schema: Schema
    generated: str
    naptan_date: str
    sources: List[str]

    @classmethod
    def from_dict(cls, header):
        schema = Schema(**header["schema"])
        return cls(
            schema=schema,
            generated=header["generated"],
            sources=header["sources"],
            naptan_date=header["naptan_date"],
        )


@final
class Report:
    def __init__(self, source):
        if hasattr(source, "read"):
            self.filename = source.name
            report = json.load(source)
        else:
            self.filename = source
            with open(source, "r") as f:
                report = json.load(f)

        self.model: Model = Model(report["model"])
        self.header: Header = Header.from_dict(report["header"])
        self.warnings: List[BaseWarning] = []
        for w in report["warnings"]:
            self.warnings += factory.build(w)

    def __str__(self):
        return f"Report - {self.filename}"

    def __repr__(self):
        return f"Report(source={self.filename!r})"

    def filter_by_warning_type(self, warning_type: StrOrList) -> List[BaseWarning]:
        if isinstance(warning_type, str):
            warning_type = [warning_type]
        return [w for w in self.warnings if w.warning_type in warning_type]

    def filter_warning_by_id(self, ito_id: str) -> List[BaseWarning]:
        return [w for w in self.warnings if w.id == ito_id]
