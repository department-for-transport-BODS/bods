import itertools
import json
from collections import defaultdict
from logging import getLogger
from pathlib import Path
from typing import Callable, List, Optional
from urllib.parse import unquote

from dateutil import parser
from dateutil.relativedelta import relativedelta
from django.db.models import CharField, Value
from django.db.models.functions import Replace
from lxml import etree

from transit_odp.common.types import JSONFile, XMLFile
from transit_odp.data_quality.pti.constants import FLEXIBLE_SERVICE, STANDARD_SERVICE
from transit_odp.data_quality.pti.functions import (
    cast_to_bool,
    cast_to_date,
    check_flexible_service_stop_point_ref,
    check_flexible_service_times,
    check_flexible_service_timing_status,
    check_inbound_outbound_description,
    check_service_group_validations,
    check_vehicle_journey_timing_links,
    contains_date,
    has_flexible_or_standard_service,
    has_flexible_service_classification,
    has_name,
    has_prohibited_chars,
    is_member_of,
    regex,
    strip,
    to_days,
    today,
    validate_bank_holidays,
    validate_line_id,
    validate_modification_date_time,
    validate_run_time,
    validate_timing_link_stops,
)
from transit_odp.data_quality.pti.models import Observation, Schema, Violation
from transit_odp.data_quality.pti.models.txcmodels import Line, VehicleJourney
from transit_odp.naptan.models import StopPoint
from transit_odp.otc.models import Service

logger = getLogger(__name__)


def has_destination_display(context, patterns):
    """
    First check if DestinationDisplay in JourneyPattern is provided.

    If not, we need to check in if DynamicDestinationDisplay is provided for
    each stop inside a JourneyPatternTimingLink.

    If both conditions above fail, then DestinationDisplay should
    mandatory nside VehicleJourney.
    """
    pattern = patterns[0]
    validator = DestinationDisplayValidator(pattern)
    return validator.validate()


def get_lines_validator(context, lines: List[etree._Element]) -> bool:
    lines = lines[0]
    stops = StopPoint.objects.exclude(stop_areas=[]).values("atco_code", "stop_areas")
    stop_area_map = {stop["atco_code"]: stop["stop_areas"] for stop in stops}
    validator = LinesValidator(lines, stop_area_map=stop_area_map)
    return validator.validate()


def validate_non_naptan_stop_points(context, points):
    point = points[0]
    validator = StopPointValidator(point)
    return validator.validate()


class BaseValidator:
    def __init__(self, root):
        self.root = root
        self.namespaces = {"x": self.root.nsmap.get(None)}

        self._vehicle_journeys = None
        self._lines = None
        self._journey_patterns = None

    @property
    def lines(self):
        if self._lines is not None:
            return self._lines
        lines = self.root.xpath("//x:Line", namespaces=self.namespaces)
        self._lines = [Line.from_xml(line) for line in lines]
        return self._lines

    @property
    def vehicle_journeys(self):
        if self._vehicle_journeys is not None:
            return self._vehicle_journeys
        xpath = "//x:VehicleJourneys/x:VehicleJourney"
        journeys = self.root.xpath(xpath, namespaces=self.namespaces)
        self._vehicle_journeys = [VehicleJourney.from_xml(vj) for vj in journeys]
        return self._vehicle_journeys

    @property
    def journey_patterns(self):
        if self._journey_patterns is not None:
            return self._journey_patterns

        xpath = "//x:JourneyPatterns/x:JourneyPattern"
        patterns = self.root.xpath(xpath, namespaces=self.namespaces)
        self._journey_patterns = patterns
        return self._journey_patterns

    def get_journey_pattern_ref_by_vehicle_journey_code(self, code: str):
        vehicle_journeys = self.get_vehicle_journey_by_code(code)

        if len(vehicle_journeys) < 1:
            return ""

        vj = vehicle_journeys[0]
        if vj.journey_pattern_ref != "":
            return vj.journey_pattern_ref
        elif vj.vehicle_journey_ref != "":
            return self.get_journey_pattern_ref_by_vehicle_journey_code(
                vj.vehicle_journey_ref
            )
        else:
            return ""

    def get_journey_pattern_refs_by_line_ref(self, ref: str):
        """
        Returns all the JourneyPatternRefs that appear in the VehicleJourneys have
        LineRef equal to ref.
        """
        jp_refs = set()
        vehicle_journeys = self.get_vehicle_journey_by_line_ref(ref)
        for journey in vehicle_journeys:
            jp_ref = self.get_journey_pattern_ref_by_vehicle_journey_code(journey.code)
            if jp_ref != "":
                jp_refs.add(jp_ref)
        return list(jp_refs)

    def get_vehicle_journey_by_line_ref(self, ref) -> List[VehicleJourney]:
        """
        Get all the VehicleJourneys that have LineRef equal to ref.
        """
        return [vj for vj in self.vehicle_journeys if vj.line_ref == ref]

    def get_vehicle_journey_by_pattern_journey_ref(self, ref) -> List[VehicleJourney]:
        """
        Get all the VehicleJourneys that JourneyPatternRef equal to ref.
        """
        return [vj for vj in self.vehicle_journeys if vj.journey_pattern_ref == ref]

    def get_vehicle_journey_by_code(self, code) -> List[VehicleJourney]:
        """
        Get the VehicleJourney with VehicleJourneyCode equal to code.
        """
        return [vj for vj in self.vehicle_journeys if vj.code == code]

    def get_route_section_by_stop_point_ref(self, ref):
        xpath = (
            "//x:RouteSections/x:RouteSection/"
            f"x:RouteLink[string(x:From/x:StopPointRef) = '{ref}' "
            f"or string(x:To/x:StopPointRef) = '{ref}']/@id"
        )
        link_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(link_refs))

    def get_journey_pattern_section_refs_by_route_link_ref(self, ref):
        xpath = (
            "//x:JourneyPatternSections/x:JourneyPatternSection"
            f"[x:JourneyPatternTimingLink[string(x:RouteLinkRef) = '{ref}']]/@id"
        )
        section_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(section_refs))

    def get_journey_pattern_ref_by_journey_pattern_section_ref(self, ref):
        xpath = f"//x:JourneyPattern[string(x:JourneyPatternSectionRefs) = '{ref}']/@id"
        journey_pattern_refs = self.root.xpath(xpath, namespaces=self.namespaces)
        return list(set(journey_pattern_refs))

    def get_stop_point_ref_from_journey_pattern_ref(self, ref):
        xpath = (
            f"//x:StandardService/x:JourneyPattern[@id='{ref}']"
            "/x:JourneyPatternSectionRefs/text()"
        )
        section_refs = self.root.xpath(xpath, namespaces=self.namespaces)

        all_stop_refs = []
        for section_ref in section_refs:
            xpath = (
                "//x:JourneyPatternSections/x:JourneyPatternSection"
                f"[@id='{section_ref}']/x:JourneyPatternTimingLink/*"
                "[local-name() = 'From' or local-name() = 'To']/x:StopPointRef/text()"
            )
            stop_refs = self.root.xpath(xpath, namespaces=self.namespaces)
            all_stop_refs += stop_refs

        return list(set(all_stop_refs))

    def get_locality_name_from_annotated_stop_point_ref(self, ref) -> Optional[str]:
        """
        Get the LocalityName of an AnnotatedStopPointRef from its StopPointRef.
        """
        xpath = (
            "//x:StopPoints//x:AnnotatedStopPointRef[string(x:StopPointRef)"
            f" = '{ref}']/x:LocalityName/text()"
        )
        names = self.root.xpath(xpath, namespaces=self.namespaces)
        if names:
            return names[0]
        return None


class DestinationDisplayValidator:
    def __init__(self, journey_pattern):
        self.namespaces = {"x": journey_pattern.nsmap.get(None)}
        self.journey_pattern = journey_pattern
        self.journey_pattern_ref = self.journey_pattern.get("id")

    @property
    def vehicle_journeys(self):
        root = self.journey_pattern.getroottree()
        xpath = (
            "//x:VehicleJourney[contains(x:JourneyPatternRef, "
            f"'{self.journey_pattern_ref}')]"
        )
        return root.xpath(xpath, namespaces=self.namespaces)

    @property
    def journey_pattern_sections(self):
        xpath = "x:JourneyPatternSectionRefs/text()"
        refs = self.journey_pattern.xpath(xpath, namespaces=self.namespaces)
        xpaths = [f"//x:JourneyPatternSection[@id='{ref}']" for ref in refs]

        sections = []
        for xpath in xpaths:
            sections += self.journey_pattern.xpath(xpath, namespaces=self.namespaces)
        return sections

    def journey_pattern_has_display(self):
        displays = self.journey_pattern.xpath(
            "x:DestinationDisplay", namespaces=self.namespaces
        )
        return len(displays) > 0

    def links_have_dynamic_displays(self):
        for section in self.journey_pattern_sections:
            links = section.xpath(
                "x:JourneyPatternTimingLink", namespaces=self.namespaces
            )
            for link in links:
                from_display = link.xpath(
                    "x:From/x:DynamicDestinationDisplay", namespaces=self.namespaces
                )
                to_display = link.xpath(
                    "x:To/x:DynamicDestinationDisplay", namespaces=self.namespaces
                )
                if not all([to_display, from_display]):
                    return False
        return True

    def vehicle_journeys_have_displays(self):
        xpath = "x:DestinationDisplay"
        for journey in self.vehicle_journeys:
            display = journey.xpath(xpath, namespaces=self.namespaces)
            if not display:
                return False

        return True

    def validate(self):
        if self.journey_pattern_has_display():
            return True

        if self.links_have_dynamic_displays():
            return True

        if self.vehicle_journeys_have_displays():
            return True

        return False


class LinesValidator(BaseValidator):
    def __init__(self, *args, stop_area_map=None, **kwargs):
        self._stop_area_map = stop_area_map or {}
        super().__init__(*args, **kwargs)

    def _flatten_stop_areas(self, stops: list[str]) -> set[str]:
        stop_areas = []
        for stop in stops:
            stop_areas += self._stop_area_map.get(stop, [])
        return set(stop_areas)

    def check_for_common_journey_patterns(self) -> bool:
        """
        Check whether related lines share a JourneyPattern with the
        designated main line.
        """
        line_to_journey_pattern = {}
        for line in self.lines:
            jp_refs = self.get_journey_pattern_refs_by_line_ref(line.ref)
            line_to_journey_pattern[line.ref] = jp_refs

        combinations = itertools.combinations(line_to_journey_pattern.keys(), 2)
        for line1, line2 in combinations:
            line1_refs = line_to_journey_pattern.get(line1)
            line2_refs = line_to_journey_pattern.get(line2)

            if set(line1_refs).isdisjoint(line2_refs):
                return False
        return True

    def check_for_common_stops_points(self) -> bool:
        """
        Check if all lines share common stop points.
        """
        line_to_stops = defaultdict(list)
        for line in self.lines:
            jp_refs = self.get_journey_pattern_refs_by_line_ref(line.ref)
            for jp_ref in jp_refs:
                stops = self.get_stop_point_ref_from_journey_pattern_ref(jp_ref)
                line_to_stops[line.ref] += stops

        combinations = itertools.combinations(line_to_stops.keys(), 2)
        for line1, line2 in combinations:
            line1_stops = line_to_stops.get(line1, [])
            line2_stops = line_to_stops.get(line2, [])
            line1_stop_areas = self._flatten_stop_areas(line1_stops)
            line2_stop_areas = self._flatten_stop_areas(line2_stops)

            disjointed_stop_areas = line1_stop_areas.isdisjoint(line2_stop_areas)
            disjointed_stops = set(line1_stops).isdisjoint(line2_stops)

            line1_localities = [
                self.get_locality_name_from_annotated_stop_point_ref(ref)
                for ref in line1_stops
            ]
            line1_localities = [name for name in line1_localities if name]
            line2_localities = [
                self.get_locality_name_from_annotated_stop_point_ref(ref)
                for ref in line2_stops
            ]
            line2_localities = [name for name in line2_localities if name]
            disjointed_localities = set(line1_localities).isdisjoint(line2_localities)

            if all([disjointed_stop_areas, disjointed_stops, disjointed_localities]):
                return False

        return True

    def validate(self) -> bool:
        """
        Validates that all Line that appears in Lines are related.

        """
        if len(self.lines) < 2:
            return True

        if self.check_for_common_journey_patterns():
            return True

        if self.check_for_common_stops_points():
            return True

        return False


class StopPointValidator(BaseValidator):
    @property
    def stop_point_ref(self):
        xpath = "string(x:AtcoCode)"
        return self.root.xpath(xpath, namespaces=self.namespaces)

    def get_operating_profile_by_vehicle_journey_code(self, ref):
        xpath = (
            f"//x:VehicleJourney[string(x:VehicleJourneyCode) = '{ref}']"
            "//x:OperatingProfile"
        )
        profiles = self.root.xpath(xpath, namespaces=self.namespaces)
        return profiles

    def get_service_operating_period(self):
        xpath = "//x:Service//x:OperatingPeriod"
        periods = self.root.xpath(xpath, namespaces=self.namespaces)
        return periods

    def has_valid_operating_profile(self, ref):
        profiles = self.get_operating_profile_by_vehicle_journey_code(ref)

        if len(profiles) < 1:
            return True
        else:
            profile = profiles[0]

        start_date = profile.xpath("string(.//x:StartDate)", namespaces=self.namespaces)
        end_date = profile.xpath("string(.//x:EndDate)", namespaces=self.namespaces)

        if start_date == "" or end_date == "":
            # If start or end date unspecified, inherit from the service's
            # OperatingPeriod
            periods = self.get_service_operating_period()
            if len(periods) > 0:
                period = periods[0]
                if start_date == "":
                    start_date = period.xpath(
                        "string(./x:StartDate)", namespaces=self.namespaces
                    )
                if end_date == "":
                    end_date = period.xpath(
                        "string(./x:EndDate)", namespaces=self.namespaces
                    )

        if start_date == "" or end_date == "":
            return False

        start_date = parser.parse(start_date)
        end_date = parser.parse(end_date)
        less_than_2_months = end_date <= start_date + relativedelta(months=2)
        return less_than_2_months

    def validate(self):
        route_link_refs = self.get_route_section_by_stop_point_ref(self.stop_point_ref)
        all_vj = []

        for link_ref in route_link_refs:
            section_refs = self.get_journey_pattern_section_refs_by_route_link_ref(
                link_ref
            )
            for section_ref in section_refs:
                jp_refs = self.get_journey_pattern_ref_by_journey_pattern_section_ref(
                    section_ref
                )
                for jp_ref in jp_refs:
                    all_vj += self.get_vehicle_journey_by_pattern_journey_ref(jp_ref)

        for journey in all_vj:
            if not self.has_valid_operating_profile(journey.code):
                return False

        return True


class ServiceCodeValidator:
    def __init__(self, service_codes: List[str]):
        self.service_codes = service_codes

    def validate(self, context, service_code: str):
        service_code = service_code[0].text
        if service_code.startswith("UZ"):
            return True

        return service_code in self.service_codes


def get_service_code_validator() -> Callable:
    service_codes = Service.objects.annotate(
        service_code=Replace(
            "registration_number",
            Value("/", output_field=CharField()),
            Value(":", output_field=CharField()),
        )
    ).values_list("service_code", flat=True)

    validator = ServiceCodeValidator(list(service_codes))
    return validator.validate


class PTIValidator:
    def __init__(self, source: JSONFile):
        json_ = json.load(source)
        self.schema = Schema(**json_)

        self.namespaces = self.schema.header.namespaces
        self.violations = []

        self.fns = etree.FunctionNamespace(None)
        self.register_function("bool", cast_to_bool)
        self.register_function("contains_date", contains_date)
        self.register_function(
            "check_flexible_service_timing_status", check_flexible_service_timing_status
        )
        self.register_function(
            "check_flexible_service_stop_point_ref",
            check_flexible_service_stop_point_ref,
        )
        self.register_function(
            "check_inbound_outbound_description",
            check_inbound_outbound_description,
        )
        self.register_function("date", cast_to_date)
        self.register_function("days", to_days)
        self.register_function("has_destination_display", has_destination_display)
        self.register_function("has_name", has_name)
        self.register_function(
            "has_flexible_or_standard_service", has_flexible_or_standard_service
        )
        self.register_function(
            "has_flexible_service_classification", has_flexible_service_classification
        )
        self.register_function("has_prohibited_chars", has_prohibited_chars)
        self.register_function(
            "check_service_group_validations", check_service_group_validations
        )
        self.register_function(
            "check_flexible_service_times",
            check_flexible_service_times,
        )
        self.register_function("in", is_member_of)
        self.register_function("regex", regex)
        self.register_function("strip", strip)
        self.register_function("today", today)
        self.register_function("validate_line_id", validate_line_id)
        self.register_function("validate_lines", get_lines_validator)
        self.register_function(
            "validate_modification_date_time", validate_modification_date_time
        )
        self.register_function(
            "validate_non_naptan_stop_points", validate_non_naptan_stop_points
        )
        self.register_function("validate_run_time", validate_run_time)
        self.register_function("validate_timing_link_stops", validate_timing_link_stops)
        self.register_function("validate_bank_holidays", validate_bank_holidays)
        self.register_function("validate_service_code", get_service_code_validator())
        self.register_function(
            "check_vehicle_journey_timing_links", check_vehicle_journey_timing_links
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

    def check_service_type(self, document):
        servie_classification_xpath = (
            "//x:Services/x:Service/x:ServiceClassification/x:Flexible"
        )
        service_classification = document.xpath(
            servie_classification_xpath, namespaces=self.namespaces
        )

        flexible_service_xpath = "//x:Services/x:Service/x:FlexibleService"
        flexible_service = document.xpath(
            flexible_service_xpath, namespaces=self.namespaces
        )

        if service_classification or flexible_service:
            return FLEXIBLE_SERVICE
        return STANDARD_SERVICE

    def is_valid(self, source: XMLFile) -> bool:
        document = etree.parse(source)
        txc_service_type = self.check_service_type(document)

        service_observations = []
        service_observations = [
            x
            for x in self.schema.observations
            if x.service_type == txc_service_type or x.service_type == "All"
        ]
        logger.info(f"Checking overvations for the XML file {source.name}")
        for observation in service_observations:
            elements = document.xpath(observation.context, namespaces=self.namespaces)
            for element in elements:
                self.check_observation(observation, element)
        logger.info(f"Completed overvations for the XML file {source.name}")
        return len(self.violations) == 0
