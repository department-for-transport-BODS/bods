import json
from pathlib import Path
from typing import Callable
from urllib.parse import unquote

from lxml import etree

from transit_odp.common.types import JSONFile, XMLFile
from transit_odp.fares_validator.types import Observation, Schema, Violation
from transit_odp.fares_validator.views.functions import (
    check_operator_id_format,
    check_public_code_length,
    check_value_of_type_of_frame_ref,
    is_time_intervals_present_in_tarrifs,
    is_fare_structure_element_present,
    is_generic_parameter_limitions_present,
    check_placement_validity_parameters,
    is_fare_zones_present_in_fare_frame,
    is_service_frame_present,
    is_lines_present_in_service_frame,
    is_schedule_stop_points,
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
        self.register_function(
            "is_fare_structure_element_present", is_fare_structure_element_present
        )
        self.register_function(
            "check_placement_validity_parameters", check_placement_validity_parameters
        )
        self.register_function(
            "is_generic_parameter_limitions_present",
            is_generic_parameter_limitions_present,
        )
        self.register_function(
            "is_fare_zones_present_in_fare_frame", is_fare_zones_present_in_fare_frame
        )
        self.register_function(
            "check_value_of_type_of_frame_ref", check_value_of_type_of_frame_ref
        )
        self.register_function("check_operator_id_format", check_operator_id_format)
        self.register_function("check_public_code_length", check_public_code_length)
        self.register_function("is_service_frame_present", is_service_frame_present)
        self.register_function(
            "is_lines_present_in_service_frame", is_lines_present_in_service_frame
        )
        self.register_function("is_schedule_stop_points", is_schedule_stop_points)

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
            for element in elements:
                self.check_observation(observation, element)
        return len(self.violations) == 0
