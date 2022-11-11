from ..constants import (
    FARE_STRUCTURE_ACCESS_RIGHT_ELIGIBILITY_REF,
    FARE_STRUCTURE_ACCESS_RIGHT_REF,
    FARE_STRUCTURE_ACCESS_RIGHT_TRAVEL_REF,
    FARE_STRUCTURE_ELEMENT_ACCESS_REF,
    FARE_STRUCTURE_ELEMENT_DURATION_REF,
    FARE_STRUCTURE_ELEMENT_ELIGIBILITY_REF,
    FARE_STRUCTURE_ELEMENT_TRAVEL_REF,
    FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING,
    LENGTH_OF_OPERATOR,
    LENGTH_OF_PUBLIC_CODE,
    NAMESPACE,
    ORG_OPERATOR_ID_SUBSTRING,
    STOP_POINT_ID_SUBSTRING,
    TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING,
    TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING,
    TYPE_OF_FRAME_REF_SUBSTRING,
    TYPE_OF_TARIFF_REF_STRING,
)
from .response import XMLViolationDetail
from .validation_messages import *


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
    try:
        type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        sourceline = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    if type_of_frame_ref_ref is not None and (
        TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
    ):
        xpath = "x:tariffs/x:Tariff/x:timeIntervals"
        time_intervals = element.xpath(xpath, namespaces=NAMESPACE)
        if not time_intervals:
            xpath = "x:tariffs/x:Tariff"
            tariff = element.xpath(xpath, namespaces=NAMESPACE)
            sourceline_time_intervals = tariff[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_time_intervals,
                MESSAGE_OBSERVATION_TARIFF_TIME_INTERVALS_MISSING,
            )
            response = response_details.__list__()
            return response


def get_individual_tariff_time_interval(element):
    element = element[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        sourceline = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    if type_of_frame_ref_ref is not None and (
        TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
    ):
        xpath = "x:tariffs/x:Tariff/x:timeIntervals/x:TimeInterval"
        time_interval = element.xpath(xpath, namespaces=NAMESPACE)
        if not time_interval:
            xpath = "x:tariffs/x:Tariff/x:timeIntervals"
            intervals = element.xpath(xpath, namespaces=NAMESPACE)
            if intervals:
                sourceline_time_interval = intervals[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_time_interval,
                    MESSAGE_OBSERVATION_TARIFF_TIME_INTERVAL_MISSING,
                )
                response = response_details.__list__()
                return response


def get_tariff_time_interval_name(element):
    element = element[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = element.xpath(xpath, namespaces=NAMESPACE)
    try:
        type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        sourceline = type_of_frame_ref[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    if type_of_frame_ref_ref is not None and (
        TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
    ):
        xpath = "x:tariffs/x:Tariff/x:timeIntervals/x:TimeInterval"
        intervals = element.xpath(xpath, namespaces=NAMESPACE)
        for interval in intervals:
            xpath = "string(x:Name)"
            name = interval.xpath(xpath, namespaces=NAMESPACE)
            if not name:
                sourceline_name = interval.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_name,
                    MESSAGE_OBSERVATION_TARIFF_NAME_MISSING,
                )
                response = response_details.__list__()
                return response


def is_individual_time_interval_present_in_tariffs(context, fare_frames, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if product_type in ["dayPass", "periodPass"]:
        return get_individual_tariff_time_interval(fare_frames)


def is_time_interval_name_present_in_tariffs(context, fare_frames, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if product_type in ["dayPass", "periodPass"]:
        return get_tariff_time_interval_name(fare_frames)


def get_fare_structure_time_intervals(element):
    """
    Checks if the fareStructureElements properties are present
    """
    xpath = "x:timeIntervals"
    time_intervals = element.xpath(xpath, namespaces=NAMESPACE)
    if not time_intervals:
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_TIME_INTERVALS_MISSING
        )
        response = response_details.__list__()
        return response
    for element in time_intervals:
        xpath = "string(x:TimeIntervalRef)"
        time_interval_ref = element.xpath(xpath, namespaces=NAMESPACE)
        if not time_interval_ref:
            sourceline = element.sourceline
            response_details = XMLViolationDetail(
                "violation", sourceline, MESSAGE_OBSERVATION_TIME_INTERVAL_REF_MISSING
            )
            response = response_details.__list__()
            return response


def get_generic_parameter_assignment_properties(element):
    """
    Checks if the FareStructureElement.GenericParameterAssignment properties are present
    """
    xpath = "//x:FareStructureElement/x:GenericParameterAssignment/x:limitations"
    limitations = element.xpath(xpath, namespaces=NAMESPACE)

    for limitation in limitations:
        xpath = "x:RoundTrip"
        round_trip = limitation.xpath(xpath, namespaces=NAMESPACE)
        if not round_trip:
            sourceline = limitation.sourceline
            response_details = XMLViolationDetail(
                "violation", sourceline, MESSAGE_OBSERVATION_ROUND_TRIP_MISSING
            )
            response = response_details.__list__()
            return response
        xpath = "x:TripType"
        trip_type = limitation.xpath(xpath, namespaces=NAMESPACE)
        if not trip_type:
            sourceline = round_trip[0].sourceline
            response_details = XMLViolationDetail(
                "violation", sourceline, MESSAGE_OBSERVATION_TRIP_TYPE_MISSING
            )
            response = response_details.__list__()
            return response


def is_time_intervals_present_in_tarrifs(context, fare_frames, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if product_type in ["dayPass", "periodPass"]:
        return get_tariff_time_intervals(fare_frames)


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
        xpath = "x:tariffs/x:Tariff/x:fareStructureElements/x:FareStructureElement"
        fare_structure_element = fare_frame.xpath(xpath, namespaces=NAMESPACE)
        for element in fare_structure_element:
            xpath = "x:TypeOfFareStructureElementRef"
            fare_structure_ref = element.xpath(xpath, namespaces=NAMESPACE)
            try:
                fare_structure_ref_ref = _extract_attribute(fare_structure_ref, "ref")
            except KeyError:
                sourceline = fare_structure_ref[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline,
                    MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
                )
                response = response_details.__list__()
                return response
            if FARE_STRUCTURE_ELEMENT_DURATION_REF == fare_structure_ref_ref:
                return get_fare_structure_time_intervals(element)


def is_generic_parameter_limitations_present(context, fare_frames, *args):
    """
    Check if ProductType is singleTrip, dayReturnTrip, periodReturnTrip.
    If true, FareStructureElement.GenericParameterAssignment elements
    should be present in Tariff.FareStructureElements
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    xpath = "x:tariffs/x:Tariff/x:fareStructureElements/x:FareStructureElement/x:TypeOfFareStructureElementRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    for type_of_frame_ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([type_of_frame_ref], "ref")
        except KeyError:
            sourceline = type_of_frame_ref.sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and FARE_STRUCTURE_ELEMENT_TRAVEL_REF == type_of_frame_ref_ref
            and product_type in ["singleTrip", "dayReturnTrip", "periodReturnTrip"]
        ):
            return get_generic_parameter_assignment_properties(fare_frame)


def is_fare_zones_present_in_fare_frame(context, fare_zones, *args):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    if fare_zones:
        xpath = "../x:TypeOfFrameRef"
        type_of_frame_ref = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            sourceline = type_of_frame_ref.sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if not (
            type_of_frame_ref_ref is not None
            and (
                TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING in type_of_frame_ref_ref
                or TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING in type_of_frame_ref_ref
            )
        ):

            sourceline_type_of_frame_ref = type_of_frame_ref[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_type_of_frame_ref,
                MESSAGE_OBSERVATION_FARE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        xpath = "//x:FareZone"
        zones = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        if not zones:
            sourceline_fare_zone = fare_zones[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_zone,
                MESSAGE_OBSERVATION_FARE_ZONE_MISSING,
            )
            response = response_details.__list__()
            return response


def is_name_present_in_fare_frame(context, fare_zones, *args):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    if fare_zones:
        xpath = "//x:FareZone"
        zones = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        for zone in zones:
            xpath = "string(x:Name)"
            name = zone.xpath(xpath, namespaces=NAMESPACE)
            if not name:
                sourceline_zone = zone.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_zone,
                    MESSAGE_OBSERVATION_FARE_ZONES_NAME_MISSING,
                )
                response = response_details.__list__()
                return response


def is_members_scheduled_point_ref_present_in_fare_frame(context, fare_zones, *args):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    if fare_zones:
        xpath = "//x:FareZone"
        zones = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        for zone in zones:
            xpath = "x:members"
            members = zone.xpath(xpath, namespaces=NAMESPACE)
            if not members:
                sourceline_zone = zone.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_zone,
                    MESSAGE_OBSERVATION_FARE_ZONES_MEMBERS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:ScheduledStopPointRef"
            schedule_stop_points = members[0].xpath(xpath, namespaces=NAMESPACE)
            sourceline_schedule_stop_points = members[0].sourceline
            if not schedule_stop_points:
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_schedule_stop_points,
                    MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_REF_MISSING,
                )
                response = response_details.__list__()
                return response
            for stop_point in schedule_stop_points:
                return get_scheduled_point_ref_text(stop_point)


def get_scheduled_point_ref_text(stop_point):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    sourceline_stop_point = stop_point.sourceline
    stop_point_text = _extract_text(stop_point)
    if not stop_point_text:
        response_details = XMLViolationDetail(
            "violation",
            sourceline_stop_point,
            MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_TEXT_MISSING,
        )
        response = response_details.__list__()
        return response


def check_value_of_type_of_frame_ref(context, data_objects, *args):
    """
    Check if TypeOfFrameRef has either UK_PI_LINE_FARE_OFFER or
    UK_PI_NETWORK_OFFER in it.
    """
    is_frame_ref_value_valid = False
    data_object = data_objects[0]
    xpath = "x:CompositeFrame"
    composite_frames = data_object.xpath(xpath, namespaces=NAMESPACE)
    for composite_frame in composite_frames:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = composite_frame.xpath(xpath, namespaces=NAMESPACE)
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            sourceline = type_of_frame_ref.sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        for ref_value in TYPE_OF_FRAME_REF_SUBSTRING:
            if ref_value in type_of_frame_ref_ref:
                is_frame_ref_value_valid = True
        if not is_frame_ref_value_valid:
            sourceline_composite_frame = type_of_frame_ref[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_composite_frame,
                MESSAGE_OBSERVATION_COMPOSITE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING,
            )
            response = response_details.__list__()
            return response


def check_operator_id_format(context, operators, *args):
    """
    Check if Operator element's id attribute in in the format - noc:xxxx
    """
    try:
        operators_id = _extract_attribute(operators, "id")
    except KeyError:
        sourceline = operators[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OPERATORS_ID_MISSING,
        )
        response = response_details.__list__()
        return response
    if (
        ORG_OPERATOR_ID_SUBSTRING not in operators_id
        and len(operators_id) != LENGTH_OF_OPERATOR
    ):
        sourceline_operator = operators[0].sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline_operator, MESSAGE_OBSERVATION_OPERATOR_ID
        )
        response = response_details.__list__()
        return response


def check_public_code_length(context, public_code, *args):
    """
    Check if PublicCode is 4 characters long
    """
    public_code_value = _extract_text(public_code)
    if public_code_value is not None:
        if len(public_code_value) != LENGTH_OF_PUBLIC_CODE:
            sourceline_public_code = public_code[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_public_code,
                MESSAGE_OBSERVATION_PUBLIC_CODE_LENGTH,
            )
            response = response_details.__list__()
            return response


def is_service_frame_present(context, service_frame, *args):
    """
    Check if ServiceFrame is present in FareFrame.
    If true, TypeOfFrameRef should include UK_PI_NETWORK
    """
    if service_frame:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = service_frame[0].xpath(xpath, namespaces=NAMESPACE)
        try:
            ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            sourceline = type_of_frame_ref.sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if ref is not None and TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING not in ref:
            sourceline_frame_ref = type_of_frame_ref[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_frame_ref,
                MESSAGE_OBSERVATION_SERVICEFRAME_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response


def is_lines_present_in_service_frame(context, service_frame, *args):
    """
    Check if ServiceFrame is present in FareFrame,
    corresponding Line properties should be present
    """
    if service_frame:
        xpath = "x:lines"
        lines = service_frame[0].xpath(xpath, namespaces=NAMESPACE)
        if lines:
            xpath = "x:Line"
            service_frame_line = lines[0].xpath(xpath, namespaces=NAMESPACE)
            if service_frame_line:
                xpath = "string(x:Name)"
                name = service_frame_line[0].xpath(xpath, namespaces=NAMESPACE)
                if not name:
                    sourceline_line = service_frame_line[0].sourceline
                    response_details = XMLViolationDetail(
                        "violation",
                        sourceline_line,
                        MESSAGE_OBSERVATION_NAME_MISSING,
                    )
                    response = response_details.__list__()
                    return response
                xpath = "string(x:PublicCode)"
                public_code = service_frame_line[0].xpath(xpath, namespaces=NAMESPACE)
                if not public_code:
                    sourceline_line = service_frame_line[0].sourceline
                    response_details = XMLViolationDetail(
                        "violation",
                        sourceline_line,
                        MESSAGE_OBSERVATION_PUBLICCODE_MISSING,
                    )
                    response = response_details.__list__()
                    return response
                xpath = "x:OperatorRef"
                operator_ref = service_frame_line[0].xpath(xpath, namespaces=NAMESPACE)
                if not operator_ref:
                    sourceline_line = service_frame_line[0].sourceline
                    response_details = XMLViolationDetail(
                        "violation",
                        sourceline_line,
                        MESSAGE_OBSERVATION_OPERATORREF_MISSING,
                    )
                    response = response_details.__list__()
                    return response
        sourceline_service_frame = service_frame[0].sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline_service_frame, MESSAGE_OBSERVATION_LINES_MISSING
        )
        response = response_details.__list__()
        return response


def is_schedule_stop_points(context, service_frame, *args):
    """
    Check if ServiceFrame is present in FareFrame,
    it's other properties should be present
    """
    if service_frame:
        xpath = "x:scheduledStopPoints"
        schedule_stop_points = service_frame[0].xpath(xpath, namespaces=NAMESPACE)
        if schedule_stop_points:
            xpath = "x:ScheduledStopPoint"
            stop_points = schedule_stop_points[0].xpath(xpath, namespaces=NAMESPACE)
            if stop_points:
                for stop in stop_points:
                    try:
                        id = _extract_attribute([stop], "id")
                    except KeyError:
                        sourceline = stop_points[0].sourceline
                        response_details = XMLViolationDetail(
                            "violation",
                            sourceline,
                            MESSAGE_STOP_POINT_ATTR_ID_MISSING,
                        )
                        response = response_details.__list__()
                        return response
                    if STOP_POINT_ID_SUBSTRING not in id:
                        sourceline_stop_point = stop.sourceline
                        response_details = XMLViolationDetail(
                            "violation",
                            sourceline_stop_point,
                            MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_ID_MISSING,
                        )
                        response = response_details.__list__()
                        return response
                    xpath = "string(x:Name)"
                    name = stop.xpath(xpath, namespaces=NAMESPACE)
                    if not name:
                        sourceline_stop_point = stop.sourceline
                        response_details = XMLViolationDetail(
                            "violation",
                            sourceline_stop_point,
                            MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_NAME_MISSING,
                        )
                        response = response_details.__list__()
                        return response
        sourceline_service_frame = service_frame[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline_service_frame,
            MESSAGE_OBSERVATION_SCHEDULED_STOP_POINTS_MISSING,
        )
        response = response_details.__list__()
        return response


def check_type_of_frame_ref_ref(context, fare_frames, *args):
    """
    Check if FareFrame TypeOfFrameRef has either UK_PI_FARE_PRODUCT or
    UK_PI_FARE_PRICE in it.
    """
    is_frame_ref_value_valid = False
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_ref:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            sourceline = type_of_frame_ref.sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        for ref_value in FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING:
            if ref_value in type_of_frame_ref_ref:
                is_frame_ref_value_valid = True
        if not is_frame_ref_value_valid:
            sourceline_fare_frame = fare_frame[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_frame,
                MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response


def all_fare_structure_element_checks(context, fare_structure_elements, *args):
    """
    1st Check: Check 'FareStructureElement' appears minimum 3 times.

    2nd Check - If 'TypeOfAccessRightAssignmentRef' and 'TypeOfFareStructureElementRef'
    elements have the correct combination of 'ref' values:

    fxc:access and fxc:can_access,
    fxc:eligibility and fxc:eligible,
    fxc:travel_conditions and fxc:condition_of_use
    """
    list_type_of_fare_structure_element_ref_ref = []
    list_type_of_access_right_assignment_ref_ref = []
    sourceline = fare_structure_elements[0].sourceline

    all_fare_structure_elements = get_fare_structure_element(fare_structure_elements)
    length_all_fare_structure_elements = len(all_fare_structure_elements)

    try:
        if length_all_fare_structure_elements > 2:
            for element in all_fare_structure_elements:
                type_of_fare_structure_element_ref = (
                    get_type_of_fare_structure_element_ref(element)
                )
                try:
                    type_of_fare_structure_element_ref_ref = _extract_attribute(
                        type_of_fare_structure_element_ref, "ref"
                    )
                except KeyError:
                    response_details = XMLViolationDetail(
                        "violation",
                        sourceline,
                        MESSAGE_TYPE_OF_FRAME_REF_MISSING,
                    )
                    response = response_details.__list__()
                    return response
                list_type_of_fare_structure_element_ref_ref.append(
                    type_of_fare_structure_element_ref_ref
                )
                type_of_access_right_assignment_ref = get_access_right_assignment_ref(
                    element
                )
                try:
                    type_of_access_right_assignment_ref_ref = _extract_attribute(
                        type_of_access_right_assignment_ref, "ref"
                    )
                except KeyError:
                    response_details = XMLViolationDetail(
                        "violation",
                        sourceline,
                        MESSAGE_TYPE_OF_FRAME_REF_MISSING,
                    )
                    response = response_details.__list__()
                    return response

                list_type_of_access_right_assignment_ref_ref.append(
                    type_of_access_right_assignment_ref_ref
                )

            access_index = list_type_of_fare_structure_element_ref_ref.index(
                FARE_STRUCTURE_ELEMENT_ACCESS_REF
            )
            can_access_index = list_type_of_access_right_assignment_ref_ref.index(
                FARE_STRUCTURE_ACCESS_RIGHT_REF
            )
            eligibility_index = list_type_of_fare_structure_element_ref_ref.index(
                FARE_STRUCTURE_ELEMENT_ELIGIBILITY_REF
            )
            eligibile_index = list_type_of_access_right_assignment_ref_ref.index(
                FARE_STRUCTURE_ACCESS_RIGHT_ELIGIBILITY_REF
            )
            travel_conditions_index = list_type_of_fare_structure_element_ref_ref.index(
                FARE_STRUCTURE_ELEMENT_TRAVEL_REF
            )
            condition_of_use_index = list_type_of_access_right_assignment_ref_ref.index(
                FARE_STRUCTURE_ACCESS_RIGHT_TRAVEL_REF
            )
    except ValueError:
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS,
        )
        response = response_details.__list__()
        return response

    # Compare indexes
    if not (
        access_index == can_access_index
        and eligibility_index == eligibile_index
        and travel_conditions_index == condition_of_use_index
    ):
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS,
        )
        response = response_details.__list__()
        return response


def check_fare_structure_element(context, fare_structure_elements, *args):
    all_fare_structure_elements = get_fare_structure_element(fare_structure_elements)
    sourceline = fare_structure_elements[0].sourceline
    if not all_fare_structure_elements:
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT
        )
        response = response_details.__list__()
        return response


def check_type_of_fare_structure_element_ref(context, fare_structure_element, *args):
    element = fare_structure_element[0]
    type_of_fare_structure_element_ref = get_type_of_fare_structure_element_ref(element)
    sourceline = element.sourceline
    if not type_of_fare_structure_element_ref:
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT_REF
        )
        response = response_details.__list__()
        return response


def check_generic_parameter(context, fare_structure_element, *args):
    element = fare_structure_element[0]
    generic_parameter = element.xpath(
        "x:GenericParameterAssignment", namespaces=NAMESPACE
    )
    sourceline = element.sourceline
    if not generic_parameter:
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_GENERIC_PARAMETER
        )
        response = response_details.__list__()
        return response


def check_access_right_assignment_ref(context, fare_structure_element, *args):
    element = fare_structure_element[0]
    access_right_assignment = get_access_right_assignment_ref(element)
    if not access_right_assignment:
        generic_parameter = element.xpath(
            "x:GenericParameterAssignment", namespaces=NAMESPACE
        )
        if generic_parameter:
            sourceline = generic_parameter[0].sourceline
            response_details = XMLViolationDetail(
                "violation", sourceline, MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT
            )
            response = response_details.__list__()
            return response
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT
        )
        response = response_details.__list__()
        return response


def get_fare_structure_element(fare_structure_elements):
    fare_structure_element = fare_structure_elements[0]
    xpath = "//x:FareStructureElement"
    return fare_structure_element.xpath(xpath, namespaces=NAMESPACE)


def get_type_of_fare_structure_element_ref(fare_structure_element):
    return fare_structure_element.xpath(
        "x:TypeOfFareStructureElementRef", namespaces=NAMESPACE
    )


def get_access_right_assignment_ref(fare_structure_element):
    return fare_structure_element.xpath(
        "x:GenericParameterAssignment/x:TypeOfAccessRightAssignmentRef",
        namespaces=NAMESPACE,
    )


def check_type_of_tariff_ref_values(context, elements, *args):
    """
    Checks if 'TypeOfTariffRef' element has acceptable 'ref' values
    """
    element = elements[0]
    xpath = "x:TypeOfTariffRef"
    is_type_of_tariff_ref = element.xpath(xpath, namespaces=NAMESPACE)
    if not is_type_of_tariff_ref:
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_TARIFF_REF_MISSING
        )
        response = response_details.__list__()
        return response
    try:
        type_of_tariff_ref_ref = _extract_attribute(is_type_of_tariff_ref, "ref")
    except KeyError:
        sourceline = is_type_of_tariff_ref[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    if not type_of_tariff_ref_ref in TYPE_OF_TARIFF_REF_STRING:
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_INCORRECT_TARIFF_REF
        )
        response = response_details.__list__()
        return response


def is_uk_pi_fare_price_frame_present(context, fare_frames, *args):
    """
    Check if mandatory fareTables elements missing for FareFrame - UK_PI_FARE_PRICE
    FareFrame UK_PI_FARE_PRICE is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline_fare_frame_ref = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_frame_ref,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareTables"
            fare_tables = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not fare_tables:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_FARE_TABLES_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:fareTables/x:FareTable"
            fare_table = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not fare_table:
                sourceline_fare_tables = fare_tables[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_tables,
                    MESSAGE_OBSERVATION_FARE_TABLE_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:fareTables/x:FareTable/x:pricesFor"
            prices_for = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not prices_for:
                sourceline_fare_table = fare_table[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_table,
                    MESSAGE_OBSERVATION_PRICES_FOR_MISSING,
                )
                response = response_details.__list__()
                return response


def check_fare_products(context, fare_frames, *args):
    """
    check if mandatory 'fareProducts' elements missing for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline_fare_frame = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_frame,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts"
            fare_products = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not fare_products:
                sourceline = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation", sourceline, MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING
                )
                response = response_details.__list__()
                return response


def check_preassigned_fare_products(context, fare_frames, *args):
    """
    Check if mandatory element 'PreassignedFareProduct' missing in fareProducts
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline_fare_frame = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_frame,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts/x:PreassignedFareProduct"
            preassigned_fare_product = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not preassigned_fare_product:
                sourceline_fare_product = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_product,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_preassigned_fare_products_name(context, fare_frames, *args):
    """
    Check if mandatory element is 'Name' present in PreassignedFareProduct
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline_fare_frame = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_frame,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:Name"
            name = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not name:
                sourceline_preassigned = fare_frame[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_preassigned,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_NAME_MISSING,
                )
                response = response_details.__list__()
                return response


def check_preassigned_fare_products_type_ref(context, fare_frames, *args):
    """
    Check if mandatory element is 'TypeOfFareProductRef' present in PreassignedFareProduct
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline_fare_frame = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_frame,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:TypeOfFareProductRef"
            type_of_fare_product = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not type_of_fare_product:
                sourceline_preassigned = fare_frame[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_preassigned,
                    MESSAGE_OBSERVATION_PREASSIGNED_TYPE_OF_FARE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_preassigned_fare_products_charging_type(context, fare_frames, *args):
    """
    Check if mandatory element is 'ChargingMomentType' present in PreassignedFareProduct
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline_fare_frame = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_frame,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:ChargingMomentType"
            charging_moment_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not charging_moment_type:
                sourceline_preassigned = fare_frame[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_preassigned,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_CHARGING_MISSING,
                )
                response = response_details.__list__()
                return response


def check_preassigned_validable_elements(context, fare_frames, *args):
    """
    Check if element 'validableElements' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:validableElements"
            validable_elements = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not validable_elements:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_ELEMENTS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:validableElements/x:ValidableElement"
            validable_element = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not validable_element:
                sourceline_validable_element = validable_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_validable_element,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_ELEMENT_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:validableElements/x:ValidableElement/x:fareStructureElements"
            fare_structure_elements = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not fare_structure_elements:
                sourceline_fare_structure = validable_element[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_structure,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_FARE_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:validableElements/x:ValidableElement/x:fareStructureElements/x:FareStructureElementRef"
            fare_structure_element_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not fare_structure_element_ref:
                sourceline_fare_structure_ref = fare_structure_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_structure_ref,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_FARE_REF_MISSING,
                )
                response = response_details.__list__()
                return response


def check_access_right_elements(context, fare_frames, *args):
    """
    Check if mandatory element 'AccessRightInProduct' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:accessRightsInProduct"
            access_right = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not access_right:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_PREASSIGNED_ACCESS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:accessRightsInProduct/x:AccessRightInProduct/x:ValidableElementRef"
            validable_element_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not validable_element_ref:
                sourceline_validable_element_ref = access_right[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_validable_element_ref,
                    MESSAGE_OBSERVATION_PREASSIGNED_ACCESS_VALIDABLE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_product_type(context, fare_frames, *args):
    """
    Check if mandatory element 'ProductType'is missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts/x:PreassignedFareProduct/x:ProductType"
            product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not product_type:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_PREASSIGNED_PRODUCT_TYPE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_sales_offer_packages(context, fare_frames, *args):
    """
    Check if mandatory salesOfferPackages elements missing for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:salesOfferPackages"
            sales_offer_packages = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_packages:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_PACKAGES_MISSING,
                )
                response = response_details.__list__()
                return response


def check_sales_offer_package(context, fare_frames, *args):
    """
    Check if mandatory element 'SalesOfferPackage' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:salesOfferPackages/x:SalesOfferPackage"
            sales_offer_package = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_package:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_PACKAGE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_distribution_assignments_elements(context, fare_frames, *args):
    """
    Check if mandatory element 'distributionAssignments' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments"
            distribution_assignments = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not distribution_assignments:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENTS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments/x:DistributionAssignment"
            distribution_assignment = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not distribution_assignment:
                sourceline_distribution_assignment = distribution_assignments[
                    0
                ].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_distribution_assignment,
                    MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENT_MISSING,
                )
                response = response_details.__list__()
                return response


def check_distribution_channel_type(context, fare_frames, *args):
    """
    Check if mandatory element 'DistributionChannelType' is missing for DistributionAssignment in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments/x:DistributionAssignment/x:DistributionChannelType"
            distribution_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not distribution_type:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_DIST_CHANNEL_TYPE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_payment_methods(context, fare_frames, *args):
    """
    Check if mandatory element 'PaymentMethods' is missing for DistributionAssignment in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments/x:DistributionAssignment/x:PaymentMethods"
            payment_method = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not payment_method:
                sourceline_fare_frame = fare_frame[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_PAYMENT_METHODS_MISSING,
                )
                response = response_details.__list__()
                return response


def check_sales_offer_elements(context, fare_frames, *args):
    """
    Check if mandatory element 'salesOfferPackageElements' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = (
                "x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements"
            )
            sales_offer_elements = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_elements:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_ELEMENTS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements/x:SalesOfferPackageElement"
            sales_offer_element = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_element:
                sourceline_sales_package_elements = sales_offer_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_sales_package_elements,
                    MESSAGE_OBSERVATION_SALES_OFFER_ELEMENT_MISSING,
                )
                response = response_details.__list__()
                return response


def check_type_of_travel_doc(context, fare_frames, *args):
    """
    Check if mandatory element 'TypeOfTravelDocumentRef' is missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements/x:SalesOfferPackageElement/x:TypeOfTravelDocumentRef"
            type_of_travel_document_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not type_of_travel_document_ref:
                sourceline_fare_frame = fare_frame[0]
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_TRAVEL_DOC_MISSING,
                )
                response = response_details.__list__()
                return response


def check_fare_product_ref(context, fare_frames, *args):
    """
    Check if mandatory element 'PreassignedFareProductRef' is missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame = fare_frames[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_TYPE_OF_FRAME_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements/x:SalesOfferPackageElement/x:PreassignedFareProductRef"
            preassigned_fare_product_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not preassigned_fare_product_ref:
                sourceline_fare_frame = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_SALES_OFFER_FARE_PROD_REF_MISSING,
                )
                response = response_details.__list__()
                return response


def check_generic_parameters_for_access(context, elements, *args):
    """
    Checks if 'GenericParameterAssignment' has acceptable elements within it when
    'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'
    """
    element = elements[0]
    xpath = "x:FareStructureElement"
    fare_structure_elements = element.xpath(xpath, namespaces=NAMESPACE)
    for fare_structure_element in fare_structure_elements:
        xpath = "x:TypeOfFareStructureElementRef"
        type_of_fare_structure_element_ref = fare_structure_element.xpath(
            xpath, namespaces=NAMESPACE
        )
        try:
            type_of_fare_structure_element_ref_ref = _extract_attribute(
                type_of_fare_structure_element_ref, "ref"
            )
        except KeyError:
            sourceline = type_of_fare_structure_element_ref[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_FARE_STRCUTURE_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if FARE_STRUCTURE_ELEMENT_ACCESS_REF == type_of_fare_structure_element_ref_ref:
            xpath = "x:GenericParameterAssignment/x:ValidityParameterGroupingType"
            grouping_type = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

            xpath = "x:GenericParameterAssignment/x:ValidityParameterAssignmentType"
            assignment_type = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

            xpath = "x:GenericParameterAssignment/x:validityParameters"
            validity_parameters = fare_structure_element.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not ((grouping_type or assignment_type) and validity_parameters):
                sourceline_fare_structure = fare_structure_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_structure,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER_ACCESS_PROPS_MISSING,
                )
                response = response_details.__list__()
                return response


def check_generic_parameters_for_eligibility(context, elements, *args):
    """
    Checks if 'GenericParameterAssignment' has acceptable elements within it when
    'TypeOfFareStructureElementRef' has a ref value of 'fxc:eligibility'
    """
    element = elements[0]
    xpath = "x:FareStructureElement"
    fare_structure_elements = element.xpath(xpath, namespaces=NAMESPACE)
    for fare_structure_element in fare_structure_elements:
        xpath = "x:TypeOfFareStructureElementRef"
        type_of_fare_structure_element_ref = fare_structure_element.xpath(
            xpath, namespaces=NAMESPACE
        )
        try:
            type_of_fare_structure_element_ref_ref = _extract_attribute(
                type_of_fare_structure_element_ref, "ref"
            )
        except KeyError:
            sourceline = type_of_fare_structure_element_ref[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_FARE_STRCUTURE_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            FARE_STRUCTURE_ELEMENT_ELIGIBILITY_REF
            == type_of_fare_structure_element_ref_ref
        ):
            xpath = "x:GenericParameterAssignment/x:limitations/x:UserProfile"
            user_profile = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

            xpath = "x:GenericParameterAssignment/x:limitations/x:UserProfile/x:Name"
            user_profile_name = fare_structure_element.xpath(
                xpath, namespaces=NAMESPACE
            )
            xpath = (
                "x:GenericParameterAssignment/x:limitations/x:UserProfile/x:UserType"
            )
            user_type = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

            if not (user_profile and user_profile_name and user_type):
                sourceline_fare_structure = fare_structure_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_structure,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER_ELIGIBILITY_PROPS_MISSING,
                )
                response = response_details.__list__()
                return response


def check_frequency_of_use(context, fare_structure_elements, *args):
    """
    Check if mandatory element 'FrequencyOfUse' or it's child missing in
    FareStructureElement with TypeOfFareStructureElementRef - fxc:travel_conditions
    """
    fare_structure_element = fare_structure_elements[0]
    xpath = "x:TypeOfFareStructureElementRef"
    type_of_frame_refs = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)
    if type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_refs, "ref")
        except KeyError:
            sourceline = type_of_frame_refs[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline,
                MESSAGE_OBSERVATION_FARE_STRCUTURE_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and FARE_STRUCTURE_ELEMENT_TRAVEL_REF == type_of_frame_ref_ref
        ):
            xpath = "x:GenericParameterAssignment/x:limitations/x:FrequencyOfUse"
            frequency_of_use = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)
            if not frequency_of_use:
                sourceline_fare_structure_element = fare_structure_element.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_structure_element,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:GenericParameterAssignment/x:limitations/x:FrequencyOfUse/x:FrequencyOfUseType"
            frequency_of_use_type = fare_structure_element.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not frequency_of_use_type:
                sourceline_use_type = frequency_of_use[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_use_type,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER_FREQUENCY_TYPE_MISSING,
                )
                response = response_details.__list__()
                return response
