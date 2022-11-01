from ast import operator
from asyncio.format_helpers import extract_stack
from lib2to3.pgen2.token import NAME
from xml.dom.expatbuilder import Namespaces
from xml.etree.ElementTree import tostring
from lxml import etree
from ..constants import (
    LENGTH_OF_OPERATOR,
    LENGTH_OF_PUBLIC_CODE,
    ORG_OPERATOR_ID_SUBSTRING,
    TYPE_OF_FRAME_REF_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    FARE_STRUCTURE_ELEMENT_REF,
    TYPE_OF_ACCESS_RIGHT_REF,
    STOP_POINT_ID_SUBSTRING,
    NAMESPACE,
)


def _extract_text(elements, default=None):
    """
    Extract text from element
    """
    if isinstance(elements, list) and len(elements) > 0:
        item = elements[0]
        if isinstance(item, str):
            text = item
        else:
            text = item.text
    elif isinstance(elements, str):
        text = elements
    elif hasattr(elements, "text"):
        text = elements.text
    else:
        text = default
    return text


def _extract_attribute(elements, attribute_name, default=None):
    """
    Extract attribute from element
    """
    if isinstance(elements, list) and len(elements) > 0:
        item = elements[0]
        try:
            element_attribute = item.attrib[attribute_name]
        except KeyError:
            element_attribute = ""
            raise KeyError

    elif isinstance(elements, str):
        try:
            element_attribute = elements.attrib[attribute_name]
        except KeyError:
            element_attribute = ""
            raise KeyError
    else:
        element_attribute = default
    return element_attribute


def get_tariff_time_intervals(element):
    """
    Checks if the tarrif element has timeIntervals
    """
    element = element[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
    if type_of_frame_ref_ref is not None and (
        TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
    ):
        xpath = "x:tariffs/x:Tariff/x:timeIntervals"
        time_intervals = element.xpath(xpath, namespaces=NAMESPACE)
        if not time_intervals:
            return False
        xpath = "x:TimeInterval"
        intervals = time_intervals[0].xpath(xpath, namespaces=NAMESPACE)
        if not intervals:
            return False
        for interval in intervals:
            xpath = "string(x:Name)"
            name = interval.xpath(xpath, namespaces=NAMESPACE)
            if not name:
                return False
        return True
    return True


def get_fare_structure_time_intervals(element):
    """
    Checks if the fareStructureElements properties are present
    """
    element = element[0]
    xpath = "../x:timeIntervals/x:TimeIntervalRef"
    time_intervals = element.xpath(xpath, namespaces=NAMESPACE)
    if time_intervals:
        return True
    return False


def get_generic_parameter_assignment_properties(element):
    """
    Checks if the fareStructureElements properties are present
    """
    xpath = "string(//x:FareStructureElement/x:GenericParameterAssignment/x:limitations/x:RoundTrip)"
    round_trip = element.xpath(xpath, namespaces=NAMESPACE)
    xpath = "string(//x:FareStructureElement/x:GenericParameterAssignment/x:limitations/x:RoundTrip/x:TripType)"
    trip_type = element.xpath(xpath, namespaces=NAMESPACE)
    if round_trip and trip_type:
        return True
    return False


def is_time_intervals_present_in_tarrifs(context, fare_frames, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    xpath = "string(//x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if product_type in ["dayPass", "periodPass"]:
        return get_tariff_time_intervals(fare_frames)
    return True


def is_fare_structure_element_present(context, fare_frames, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, FareStructureElement elements
    should be present in Tariff.FareStructureElements
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if product_type in ["dayPass", "periodPass"]:
        xpath = "x:tariffs/x:Tariff/x:fareStructureElements/x:FareStructureElement/x:TypeOfFareStructureElementRef"
        fare_structure_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
        try:
            fare_structure_ref_ref = _extract_attribute(fare_structure_ref, "ref")
        except KeyError:
            return False
        if FARE_STRUCTURE_ELEMENT_REF == fare_structure_ref_ref:
            return get_fare_structure_time_intervals(fare_structure_ref)
    return True


def is_generic_parameter_limitions_present(context, fare_frames, *args):
    """
    Check if ProductType is singleTrip, dayReturnTrip, periodReturnTrip.
    If true, FareStructureElement.GenericParameterAssignment elements should be present in Tariff.FareStructureElements
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if product_type in ["singleTrip", "dayReturnTrip", "periodReturnTrip"]:
        return get_generic_parameter_assignment_properties(fare_frame)
    return True


def check_placement_validity_parameters(context, element, *args):
    """
    Check for validityParameters.
    It should either be nested within GenericParameterAssignment.ValidityParameterGroupingType
    or GenericParameterAssignment.ValidityParameterAssignmentType",
    """
    element = element[0]
    xpath = "x:TypeOfAccessRightAssignmentRef"
    assignment_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        assignment_ref_ref = _extract_attribute(assignment_ref, "ref")
    except KeyError:
        return False
    if TYPE_OF_ACCESS_RIGHT_REF == assignment_ref_ref:
        xpath = "string(x:ValidityParameterGroupingType/x:validityParameters)"
        in_grouping_type = element.xpath(xpath, namespaces=NAMESPACE)
        xpath = "string(x:ValidityParameterAssignmentType/x:validityParameters)"
        in_assignment_type = element.xpath(xpath, namespaces=NAMESPACE)
        if in_grouping_type or in_assignment_type:
            return True
        return False
    return True


def is_fare_zones_present_in_fare_frame(context, fare_zones, *args):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    if fare_zones:
        xpath = "..//x:TypeOfFrameRef"
        type_of_frame_ref = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            return False
        if TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING not in type_of_frame_ref_ref:
            return False
        xpath = "//x:FareZone"
        zones = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        if not zones:
            return False
        for zone in zones:
            xpath = "string(x:Name)"
            name = zone.xpath(xpath, namespaces=NAMESPACE)
            xpath = "x:members"
            members = zone.xpath(xpath, namespaces=NAMESPACE)
            if not name or not members:
                return False
            xpath = "x:ScheduledStopPointRef"
            schedule_stop_points = members[0].xpath(xpath, namespaces=NAMESPACE)
            if not schedule_stop_points:
                return False
            for stop_point in schedule_stop_points:
                stop_point_text = _extract_text(stop_point)
                if not stop_point_text:
                    return False
        return True


def check_value_of_type_of_frame_ref(context, type_of_frame_ref, *args):
    """
    Check if TypeOfFrameRef has either UK_PI_LINE_FARE_OFFER or
    UK_PI_NETWORK_OFFER in it.
    """
    try:
        type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return False
    is_present = False
    for ref_value in TYPE_OF_FRAME_REF_SUBSTRING:
        if ref_value in type_of_frame_ref_ref:
            is_present = True
            break
    return is_present


def check_operator_id_format(context, operators, *args):
    """
    Check if Operator element's id attribute in in the format - noc:xxxx
    """
    try:
        operators_id = _extract_attribute(operators, "id")
    except KeyError:
        return False
    if (
        ORG_OPERATOR_ID_SUBSTRING in operators_id
        and len(operators_id) == LENGTH_OF_OPERATOR
    ):
        return True
    return False


def check_public_code_length(context, public_code, *args):
    """
    Check if PublicCode is 4 characters long
    """
    public_code_value = _extract_text(public_code)
    if public_code_value is not None:
        if len(public_code_value) == LENGTH_OF_PUBLIC_CODE:
            return True
    return False


def is_service_frame_present(context, service_frame, *args):
    """
    Check if ServiceFrame is present in FareFrame. If true, TypeOfFrameRef should include UK_PI_NETWORK
    """
    if service_frame:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = service_frame[0].xpath(xpath, namespaces=NAMESPACE)
        try:
            ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            return False
        if TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING in ref:
            return True
        return False


def is_lines_present_in_service_frame(context, lines, *args):
    """
    Check if ServiceFrame is present in FareFrame. If true, TypeOfFrameRef should include UK_PI_NETWORK
    """
    if lines:
        xpath = "//x:Line"
        service_frame_lines = lines[0].xpath(xpath, namespaces=NAMESPACE)
        if service_frame_lines:
            xpath = "string(x:Name)"
            name = service_frame_lines[0].xpath(xpath, namespaces=NAMESPACE)
            xpath = "string(x:PublicCode)"
            public_code = service_frame_lines[0].xpath(xpath, namespaces=NAMESPACE)
            xpath = "x:OperatorRef"
            operator_ref = service_frame_lines[0].xpath(xpath, namespaces=NAMESPACE)
            if name and public_code and operator_ref:
                return True
            return False
        return False


def is_schedule_stop_points(context, schedule_stop_points, *args):
    """
    Check if ServiceFrame is present in FareFrame. If true, TypeOfFrameRef should include UK_PI_NETWORK
    """
    if schedule_stop_points:
        xpath = "//x:ScheduledStopPoint"
        stop_points = schedule_stop_points[0].xpath(xpath, namespaces=NAMESPACE)
        if stop_points:
            for stop in stop_points:
                id = _extract_attribute([stop], "id")
                xpath = "string(x:Name)"
                name = stop.xpath(xpath, namespaces=NAMESPACE)
                if STOP_POINT_ID_SUBSTRING not in id or not name:
                    return False
            return True
        return False
