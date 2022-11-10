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
    TYPE_OF_TARIFF_REF_SUBSTRING,
)
from .response import XMLViolationDetail
from .validation_messages import (
    MESSAGE_GENERIC_PARA_ASSIGNEMENT_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
    MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT,
    MESSAGE_OBSERVATION_COMPOSITE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING,
    MESSAGE_OBSERVATION_FARE_FRAME_TYPE_OF_FRAME_REF_REF_MISSING,
    MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING,
    MESSAGE_OBSERVATION_FARE_STRUCTURE_COMBINATIONS,
    MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT,
    MESSAGE_OBSERVATION_FARE_STRUCTURE_ELEMENT_REF,
    MESSAGE_OBSERVATION_FARE_ZONE_MISSING,
    MESSAGE_OBSERVATION_FARE_ZONES_MEMBERS_MISSING,
    MESSAGE_OBSERVATION_FARE_ZONES_NAME_MISSING,
    MESSAGE_OBSERVATION_GENERIC_PARAMETER,
    MESSAGE_OBSERVATION_LINES_MISSING,
    MESSAGE_OBSERVATION_NAME_MISSING,
    MESSAGE_OBSERVATION_OPERATOR_ID,
    MESSAGE_OBSERVATION_OPERATORREF_MISSING,
    MESSAGE_OBSERVATION_PUBLIC_CODE_LENGTH,
    MESSAGE_OBSERVATION_PUBLICCODE_MISSING,
    MESSAGE_OBSERVATION_ROUND_TRIP_MISSING,
    MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_ID_MISSING,
    MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_NAME_MISSING,
    MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_REF_MISSING,
    MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_TEXT_MISSING,
    MESSAGE_OBSERVATION_SCHEDULED_STOP_POINTS_MISSING,
    MESSAGE_OBSERVATION_SERVICEFRAME_TYPE_OF_FRAME_REF_MISSING,
    MESSAGE_OBSERVATION_TARIFF_NAME_MISSING,
    MESSAGE_OBSERVATION_TARIFF_TIME_INTERVAL_MISSING,
    MESSAGE_OBSERVATION_TARIFF_TIME_INTERVALS_MISSING,
    MESSAGE_OBSERVATION_TIME_INTERVAL_REF_MISSING,
    MESSAGE_OBSERVATION_TIME_INTERVALS_MISSING,
    MESSAGE_OBSERVATION_TRIP_TYPE_MISSING,
    MESSAGE_OBSERVATION_TYPE_OF_FARE_FRAME_REF_MISSING,
    MESSAGE_OPERATORS_ID_MISSING,
    MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
    MESSAGE_TYPE_OF_FRAME_REF_MISSING,
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
    type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
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
    type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
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
                MESSAGE_GENERIC_PARA_ASSIGNEMENT_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
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
        xpath = "..//x:TypeOfFrameRef"
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
        if TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING not in type_of_frame_ref_ref:
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
            sourceline_fare_zone = zones[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_fare_zone,
                MESSAGE_OBSERVATION_FARE_ZONE_MISSING,
            )
            response = response_details.__list__()
            return response


def is_name_present_in_fare_frame(context, fare_zones, *args):
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
        sourceline_frame_ref = type_of_frame_ref[0].sourceline
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
        if TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING not in ref:
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
                    id = _extract_attribute([stop], "id")
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


def check_type_of_frame_ref_ref(context, composite_frames, *args):
    """
    Check if FareFrame TypeOfFrameRef has either UK_PI_FARE_PRODUCT or
    UK_PI_FARE_PRICE in it.
    """
    is_frame_ref_value_valid = False
    composite_frame = composite_frames[0]
    xpath = "//x:frames/x:FareFrame"
    fare_frames = composite_frame.xpath(xpath, namespaces=NAMESPACE)
    for fare_frame in fare_frames:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
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
                type_of_fare_structure_element_ref_ref = _extract_attribute(
                    type_of_fare_structure_element_ref, "ref"
                )
                list_type_of_fare_structure_element_ref_ref.append(
                    type_of_fare_structure_element_ref_ref
                )
                type_of_access_right_assignment_ref = get_access_right_assignment_ref(
                    element
                )
                type_of_access_right_assignment_ref_ref = _extract_attribute(
                    type_of_access_right_assignment_ref, "ref"
                )
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
    try:
        type_of_tariff_ref_ref = _extract_attribute(elements, "ref")
    except KeyError:
        return False
    for ref_value in TYPE_OF_TARIFF_REF_SUBSTRING:
        if type_of_tariff_ref_ref in ref_value:
            return True
    return False


def is_uk_pi_fare_price_frame_present(context, data_objects, *args):
    """
    Mandatory fareTables elements missing for FareFrame - UK_PI_FARE_PRICE
    FareFrame UK_PI_FARE_PRICE is mandatory
    """
    data_object = data_objects[0]
    xpath = "x:CompositeFrame/x:frames/x:FareFrame/x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_FARE_TABLES_REF_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:CompositeFrame/x:frames/x:FareFrame/x:fareTables"
            fare_tables = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not fare_tables:
                return False
            xpath = "x:CompositeFrame/x:frames/x:FareFrame/x:fareTables/x:FareTable"
            fare_table = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not fare_table:
                return False
            xpath = "x:CompositeFrame/x:frames/x:FareFrame/x:fareTables/x:FareTable/x:pricesFor"
            prices_for = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not prices_for:
                return False
            return True
    return False


def check_fare_products(context, data_objects, *args):
    """
    Mandatory fareProducts elements missing for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    xpath = "x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        sourceline = data_object.sourceline
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            response_details = XMLViolationDetail(
                "violation", sourceline, MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING
            )
            response = response_details.__list__()
            return response
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = "x:fareProducts"
            fare_products = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not fare_products:
                response_details = XMLViolationDetail(
                    "violation", sourceline, MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING
                )
                response = response_details.__list__()
                return response


def check_preassigned_fare_products(context, data_objects, *args):
    """
    Mandatory element 'PreassignedFareProduct' or it's children missing in
    fareProducts for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct"
            preassigned_fare_product = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not preassigned_fare_product:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:ProductType"
            product_type = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not product_type:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:Name"
            name = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not name:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:TypeOfFareProductRef"
            type_of_fare_product = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not type_of_fare_product:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:ChargingMomentType"
            charging_moment_type = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not charging_moment_type:
                return False
            return True
    return False


def check_preassigned_validable_elements(context, data_objects, *args):
    """
    Mandatory element 'validableElements' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:validableElements"
            validable_elements = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not validable_elements:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:validableElements/x:ValidableElement"
            validable_element = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not validable_element:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:validableElements/x:ValidableElement/x:fareStructureElements"
            fare_structure_elements = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not fare_structure_elements:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:validableElements/x:ValidableElement/x:fareStructureElements/x:FareStructureElementRef"
            fare_structure_element_ref = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not fare_structure_element_ref:
                return False
            return True
    return False


def check_access_right_elements(context, data_objects, *args):
    """
    Mandatory element 'AccessRightInProduct' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:accessRightsInProduct"
            access_right = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not access_right:
                return False
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:accessRightsInProduct/x:AccessRightInProduct/x:ValidableElementRef"
            validable_element_ref = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not validable_element_ref:
                return False
            return True
    return False


def check_product_type(context, data_objects, *args):
    """
    Mandatory element 'ProductType'is missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:fareProducts/x:PreassignedFareProduct/x:ProductType"
            product_type = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not product_type:
                return False
            return True
    return False


def check_sales_offer_packages(context, data_objects, *args):
    """
    Mandatory salesOfferPackages elements missing for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:salesOfferPackages"
            sales_offer_packages = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_packages:
                return False
            return True
    return False


def check_sales_offer_package(context, data_objects, *args):
    """
    Mandatory element 'SalesOfferPackage' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage"
            sales_offer_package = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_package:
                return False
            return True
    return False


def check_distribution_assignments_elements(context, data_objects, *args):
    """
    Mandatory element 'distributionAssignments' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments"
            distribution_assignments = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not distribution_assignments:
                return False
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments/x:DistributionAssignment"
            distribution_assignment = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not distribution_assignment:
                return False
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments/x:DistributionAssignment/x:DistributionChannelType"
            distribution_type = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not distribution_type:
                return False
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments/x:DistributionAssignment/x:PaymentMethods"
            payment_method = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not payment_method:
                return False
            return True
    return False


def check_sales_offer_elements(context, data_objects, *args):
    """
    Mandatory element 'salesOfferPackageElements' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/"
    xpath = f"{base_xpath}x:TypeOfFrameRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements"
            sales_offer_elements = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_elements:
                return False
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements/x:SalesOfferPackageElement"
            sales_offer_element = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not sales_offer_element:
                return False
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements/x:SalesOfferPackageElement/x:TypeOfTravelDocumentRef"
            type_of_travel_document_ref = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not type_of_travel_document_ref:
                return False
            xpath = f"{base_xpath}x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements/x:SalesOfferPackageElement/x:PreassignedFareProductRef"
            preassigned_fare_product_ref = data_object.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not preassigned_fare_product_ref:
                return False
            return True
    return False


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
            return False
        if FARE_STRUCTURE_ELEMENT_ACCESS_REF == type_of_fare_structure_element_ref_ref:
            xpath = "x:GenericParameterAssignment/x:ValidityParameterGroupingType"
            grouping_type = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

            xpath = "x:GenericParameterAssignment/x:ValidityParameterAssignmentType"
            assignment_type = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)

            xpath = "x:GenericParameterAssignment/x:validityParameters"
            validity_parameters = fare_structure_element.xpath(
                xpath, namespaces=NAMESPACE
            )

            if (grouping_type or assignment_type) and validity_parameters:
                return True
            return False
    return True


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
            return False
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

            if user_profile and user_profile_name and user_type:
                return True
            return False
    return True


def check_frequency_of_use(context, data_objects, *args):
    """
    Mandatory element 'FrequencyOfUse' or it's child missing in
    FareStructureElement with TypeOfFareStructureElementRef - fxc:travel_conditions
    """
    data_object = data_objects[0]
    base_xpath = "x:CompositeFrame/x:frames/x:FareFrame/x:tariffs/x:Tariff/x:fareStructureElements/x:FareStructureElement/"
    xpath = f"{base_xpath}x:TypeOfFareStructureElementRef"
    type_of_frame_refs = data_object.xpath(xpath, namespaces=NAMESPACE)
    for ref in type_of_frame_refs:
        try:
            type_of_frame_ref_ref = _extract_attribute([ref], "ref")
        except KeyError:
            return False
        if (
            type_of_frame_ref_ref is not None
            and FARE_STRUCTURE_ELEMENT_TRAVEL_REF == type_of_frame_ref_ref
        ):
            xpath = f"{base_xpath}x:GenericParameterAssignment/x:limitations/x:FrequencyOfUse"
            frequency_of_use = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not frequency_of_use:
                return False
            xpath = f"{base_xpath}x:GenericParameterAssignment/x:limitations/x:FrequencyOfUse/x:FrequencyOfUseType"
            frequency_of_use_type = data_object.xpath(xpath, namespaces=NAMESPACE)
            if not frequency_of_use_type:
                return False
            return True
    return False
