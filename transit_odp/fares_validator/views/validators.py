import json
from pathlib import Path
from typing import Callable
from urllib.parse import unquote

from lxml import etree

from transit_odp.common.types import JSONFile, XMLFile
from transit_odp.fares_validator.types import Observation, Schema, Violation
from transit_odp.fares_validator.views.functions import (
    all_fare_structure_element_checks,
    check_access_right_assignment_ref,
    check_access_right_elements,
    check_composite_frame_valid_between,
    check_distribution_assignments_elements,
    check_distribution_channel_type,
    check_fare_product_ref,
    check_fare_products,
    check_fare_structure_element,
    check_frequency_of_use,
    check_generic_parameter,
    check_generic_parameters_for_access,
    check_generic_parameters_for_eligibility,
    check_payment_methods,
    check_preassigned_fare_products,
    check_preassigned_fare_products_charging_type,
    check_preassigned_fare_products_name,
    check_preassigned_fare_products_type_ref,
    check_preassigned_validable_elements,
    check_product_type,
    check_resource_frame_operator_name,
    check_resource_frame_organisation_elements,
    check_sales_offer_elements,
    check_sales_offer_package,
    check_sales_offer_packages,
    check_tariff_basis,
    check_tariff_operator_ref,
    check_tariff_validity_conditions,
    check_type_of_fare_structure_element_ref,
    check_type_of_frame_ref_ref,
    check_type_of_tariff_ref_values,
    check_type_of_travel_doc,
    check_value_of_type_of_frame_ref,
    is_fare_structure_element_present,
    is_fare_zones_present_in_fare_frame,
    is_generic_parameter_limitations_present,
    is_individual_time_interval_present_in_tariffs,
    is_lines_present_in_service_frame,
    is_members_scheduled_point_ref_present_in_fare_frame,
    is_name_present_in_fare_frame,
    is_schedule_stop_points,
    is_service_frame_present,
    is_time_interval_name_present_in_tariffs,
    is_time_intervals_present_in_tarrifs,
    is_uk_pi_fare_price_frame_present,
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
            "is_individual_time_interval_present_in_tariffs",
            is_individual_time_interval_present_in_tariffs,
        )
        self.register_function(
            "is_time_interval_name_present_in_tariffs",
            is_time_interval_name_present_in_tariffs,
        )
        self.register_function(
            "is_fare_structure_element_present", is_fare_structure_element_present
        )
        self.register_function(
            "is_generic_parameter_limitations_present",
            is_generic_parameter_limitations_present,
        )
        self.register_function(
            "is_fare_zones_present_in_fare_frame", is_fare_zones_present_in_fare_frame
        )
        self.register_function(
            "check_value_of_type_of_frame_ref", check_value_of_type_of_frame_ref
        )
        self.register_function("is_service_frame_present", is_service_frame_present)
        self.register_function(
            "is_lines_present_in_service_frame", is_lines_present_in_service_frame
        )
        self.register_function("is_schedule_stop_points", is_schedule_stop_points)
        self.register_function(
            "all_fare_structure_element_checks", all_fare_structure_element_checks
        )
        self.register_function(
            "check_fare_structure_element", check_fare_structure_element
        )
        self.register_function(
            "check_type_of_fare_structure_element_ref",
            check_type_of_fare_structure_element_ref,
        )
        self.register_function("check_generic_parameter", check_generic_parameter)
        self.register_function(
            "check_access_right_assignment_ref", check_access_right_assignment_ref
        )
        self.register_function(
            "check_type_of_frame_ref_ref", check_type_of_frame_ref_ref
        )
        self.register_function(
            "check_type_of_tariff_ref_values", check_type_of_tariff_ref_values
        )
        self.register_function("check_tariff_operator_ref", check_tariff_operator_ref)
        self.register_function("check_tariff_basis", check_tariff_basis)
        self.register_function(
            "check_tariff_validity_conditions", check_tariff_validity_conditions
        )
        self.register_function(
            "is_uk_pi_fare_price_frame_present", is_uk_pi_fare_price_frame_present
        )
        self.register_function("check_fare_products", check_fare_products)
        self.register_function(
            "check_preassigned_fare_products", check_preassigned_fare_products
        )
        self.register_function(
            "check_preassigned_fare_products_name", check_preassigned_fare_products_name
        )
        self.register_function(
            "check_preassigned_fare_products_type_ref",
            check_preassigned_fare_products_type_ref,
        )
        self.register_function(
            "check_preassigned_fare_products_charging_type",
            check_preassigned_fare_products_charging_type,
        )
        self.register_function(
            "check_preassigned_validable_elements", check_preassigned_validable_elements
        )
        self.register_function(
            "check_access_right_elements", check_access_right_elements
        )
        self.register_function("check_product_type", check_product_type)
        self.register_function("check_sales_offer_packages", check_sales_offer_packages)
        self.register_function("check_sales_offer_package", check_sales_offer_package)
        self.register_function(
            "check_distribution_assignments_elements",
            check_distribution_assignments_elements,
        )
        self.register_function(
            "check_distribution_channel_type", check_distribution_channel_type
        )
        self.register_function(
            "check_payment_methods",
            check_payment_methods,
        )
        self.register_function("check_sales_offer_elements", check_sales_offer_elements)
        self.register_function("check_type_of_travel_doc", check_type_of_travel_doc)
        self.register_function("check_fare_product_ref", check_fare_product_ref)
        self.register_function(
            "check_generic_parameters_for_access", check_generic_parameters_for_access
        )
        self.register_function(
            "check_generic_parameters_for_eligibility",
            check_generic_parameters_for_eligibility,
        )
        self.register_function(
            "check_frequency_of_use",
            check_frequency_of_use,
        )
        self.register_function(
            "is_name_present_in_fare_frame", is_name_present_in_fare_frame
        )
        self.register_function(
            "is_members_scheduled_point_ref_present_in_fare_frame",
            is_members_scheduled_point_ref_present_in_fare_frame,
        )
        self.register_function(
            "check_composite_frame_valid_between", check_composite_frame_valid_between
        )
        self.register_function(
            "check_resource_frame_organisation_elements",
            check_resource_frame_organisation_elements,
        )
        self.register_function(
            "check_resource_frame_operator_name", check_resource_frame_operator_name
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
            if len(result):
                name = element.xpath("local-name(.)", namespaces=self.namespaces)
                violation = Violation(
                    line=result[1],
                    name=name,
                    filename=unquote(Path(element.base).name),
                    observation=result[2],
                    element_text=element.text,
                )
                self.add_violation(violation)

    def is_valid(self, source: XMLFile) -> bool:
        document = etree.parse(source)
        for observation in self.schema.observations:
            elements = document.xpath(observation.context, namespaces=self.namespaces)
            for element in elements:
                self.check_observation(observation, element)
        return len(self.violations) == 0
