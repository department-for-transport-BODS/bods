import json
from pathlib import Path
from typing import Callable, List, Optional
from urllib.parse import unquote

from lxml import etree

from transit_odp.common.types import JSONFile, XMLFile
from transit_odp.fares_validator.types import Observation, Schema, Violation

from transit_odp.fares_validator.views.functions import (
    is_time_intervals_present_in_tarrifs,
)


class FaresValidator:
    def __init__(self, source: JSONFile):
        json_ = json.load(source)
        self.schema = Schema(**json_)
        self.namespaces = self.schema.header.namespaces
        self.violations = []

        self.fns = etree.FunctionNamespace(None)
        self.register_function(
            "is_time_intervals_present_in_tarrifs", is_time_intervals_present_in_tarrifs
        )

    def register_function(self, key: str, function: Callable) -> None:
        self.fns[key] = function

    def add_violation(self, violation: Violation) -> None:
        self.violations.append(violation)

    def check_observation(
        self, observation: Observation, element: etree._Element
    ) -> None:
        for rule in observation.rules:
            result = element.xpath(rule.test, namespaces=self.namespaces)
            if not result:
                name = element.xpath("local-name(.)", namespaces=self.namespaces)
                violation = Violation(
                    line=element.sourceline,
                    name=name,
                    filename=unquote(Path(element.base).name),
                    observation=observation,
                    element_text=element.text,
                )
                self.add_violation(violation)
                break

    def is_valid(self, source: XMLFile) -> bool:
        document = etree.parse(source)
        for observation in self.schema.observations:
            elements = document.xpath(observation.context, namespaces=self.namespaces)
            self.check_observation(observation, elements[0])
        return len(self.violations) == 0
