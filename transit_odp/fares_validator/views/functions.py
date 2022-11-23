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
    TYPE_OF_FRAME_METADATA_SUBSTRING,
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
        xpath = "x:TimeIntervalRef"
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
    xpath = "x:GenericParameterAssignment"
    generic_parameter_assignment = element.xpath(xpath, namespaces=NAMESPACE)
    if not generic_parameter_assignment:
        sourceline_generic_parameter = element.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline_generic_parameter,
            MESSAGE_OBSERVATION_GENERIC_PARAMETER,
        )
        response = response_details.__list__()
        return response
    xpath = "x:limitations"
    limitations = generic_parameter_assignment[0].xpath(xpath, namespaces=NAMESPACE)

    if not limitations:
        sourceline = generic_parameter_assignment[0].sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATION
        )
        response = response_details.__list__()
        return response
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
        trip_type = round_trip[0].xpath(xpath, namespaces=NAMESPACE)
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
    xpath = "x:tariffs/x:Tariff/x:fareStructureElements/x:FareStructureElement"
    fare_structure_elements = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    for fare_structure_element in fare_structure_elements:
        xpath = "x:TypeOfFareStructureElementRef"
        type_of_frame_ref = fare_structure_element.xpath(xpath, namespaces=NAMESPACE)
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            sourceline = type_of_frame_ref[0].sourceline
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
            return get_generic_parameter_assignment_properties(fare_structure_element)


def is_fare_zones_present_in_fare_frame(context, fare_zones, *args):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    if fare_zones:
        xpath = "../x:TypeOfFrameRef"
        type_of_frame_ref = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        if type_of_frame_ref:
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
            if not (
                type_of_frame_ref_ref is not None
                and (
                    TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING in type_of_frame_ref_ref
                    or TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING
                    in type_of_frame_ref_ref
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
            xpath = "x:FareZone"
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
        xpath = "../x:TypeOfFrameRef"
        type_of_frame_ref = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        if type_of_frame_ref:
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
            if not (
                type_of_frame_ref_ref is not None
                and (
                    TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING in type_of_frame_ref_ref
                    or TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING
                    in type_of_frame_ref_ref
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
        xpath = "../x:TypeOfFrameRef"
        type_of_frame_ref = fare_zones[0].xpath(xpath, namespaces=NAMESPACE)
        if type_of_frame_ref:
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
            if not (
                type_of_frame_ref_ref is not None
                and (
                    TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING in type_of_frame_ref_ref
                    or TYPE_OF_FRAME_REF_SERVICE_FRAME_SUBSTRING
                    in type_of_frame_ref_ref
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


def check_value_of_type_of_frame_ref(context, composite_frames, *args):
    """
    Check if TypeOfFrameRef has either UK_PI_LINE_FARE_OFFER or
    UK_PI_NETWORK_OFFER in it.
    """
    is_frame_ref_value_valid = False
    composite_frame = composite_frames[0]
    try:
        composite_frame_id = _extract_attribute(composite_frames, "id")
    except KeyError:
        sourceline = composite_frame.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING,
        )
        response = response_details.__list__()
        return response
    if TYPE_OF_FRAME_METADATA_SUBSTRING not in composite_frame_id:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = composite_frame.xpath(xpath, namespaces=NAMESPACE)
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
    Check if ServiceFrame is present,
    corresponding Line properties should be present
    """
    if service_frame:
        xpath = "x:lines"
        lines = service_frame[0].xpath(xpath, namespaces=NAMESPACE)
        if lines:
            xpath = "x:Line"
            service_frame_line = lines[0].xpath(xpath, namespaces=NAMESPACE)
            if not service_frame_line:
                sourceline_line = lines[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_line,
                    MESSAGE_OBSERVATION_LINE_MISSING,
                )
                response = response_details.__list__()
                return response
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


def check_lines_public_code_present(context, lines, *args):
    """
    Check ServiceFrame.lines.Line.PublicCode is present
    """
    line = lines[0]
    xpath = "string(x:PublicCode)"
    public_code = line.xpath(xpath, namespaces=NAMESPACE)
    if not public_code:
        sourceline_line = line.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline_line,
            MESSAGE_OBSERVATION_PUBLICCODE_MISSING,
        )
        response = response_details.__list__()
        return response


def check_lines_operator_ref_present(context, lines, *args):
    """
    Check ServiceFrame.lines.Line.OperatorRef is present
    """
    line = lines[0]
    xpath = "x:OperatorRef"
    operator_ref = line.xpath(xpath, namespaces=NAMESPACE)
    if not operator_ref:
        sourceline_line = line.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline_line,
            MESSAGE_OBSERVATION_OPERATORREF_MISSING,
        )
        response = response_details.__list__()
        return response


def is_schedule_stop_points(context, service_frame, *args):
    """
    Check if ServiceFrame is present,
    corresponding scheduledStopPoints properties should be present
    """
    if service_frame:
        xpath = "x:scheduledStopPoints"
        schedule_stop_points = service_frame[0].xpath(xpath, namespaces=NAMESPACE)
        if schedule_stop_points:
            xpath = "x:ScheduledStopPoint"
            stop_points = schedule_stop_points[0].xpath(xpath, namespaces=NAMESPACE)
            if not stop_points:
                sourceline_stop_point = stop_points[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_stop_point,
                    MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_MISSING,
                )
                response = response_details.__list__()
                return response
            for stop in stop_points:
                try:
                    id = _extract_attribute([stop], "id")
                except KeyError:
                    sourceline = stop.sourceline
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
                        MESSAGE_OBSERVATION_SCHEDULED_STOP_POINT_ID_FORMAT,
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


def check_type_of_frame_ref_ref(context, composite_frames, *args):
    """
    Check if FareFrame TypeOfFrameRef has either UK_PI_FARE_PRODUCT or
    UK_PI_FARE_PRICE in it.
    """
    is_frame_ref_value_valid = False
    composite_frame = composite_frames[0]
    try:
        composite_frame_id = _extract_attribute(composite_frames, "id")
    except KeyError:
        sourceline = composite_frame.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING,
        )
        response = response_details.__list__()
        return response
    if TYPE_OF_FRAME_METADATA_SUBSTRING not in composite_frame_id:
        xpath = "x:frames/x:FareFrame"
        fare_frames = composite_frame.xpath(xpath, namespaces=NAMESPACE)
        for fare_frame in fare_frames:
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
            sourceline_fare_frame = composite_frame.sourceline
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
                        MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
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
                        MESSAGE_TYPE_OF_ACCESS_RIGHT_REF_MISSING,
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
            MESSAGE_OBSERVATION_TYPE_OF_TARIFF_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    if type_of_tariff_ref_ref not in TYPE_OF_TARIFF_REF_STRING:
        sourceline = element.sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_INCORRECT_TARIFF_REF
        )
        response = response_details.__list__()
        return response


def check_tariff_operator_ref(context, tariffs, *args):
    tariff = tariffs[0]
    xpath = "x:OperatorRef"
    operator_ref = tariff.xpath(xpath, namespaces=NAMESPACE)
    if not operator_ref:
        sourceline = tariff.sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_TARIFF_OPERATOR_REF_MISSING
        )
        response = response_details.__list__()
        return response


def check_tariff_basis(context, tariffs, *args):
    tariff = tariffs[0]
    xpath = "x:TariffBasis"
    tariff_basis = tariff.xpath(xpath, namespaces=NAMESPACE)
    if not tariff_basis:
        sourceline = tariff.sourceline
        response_details = XMLViolationDetail(
            "violation", sourceline, MESSAGE_OBSERVATION_TARIFF_TARIFF_BASIS_MISSING
        )
        response = response_details.__list__()
        return response


def check_tariff_validity_conditions(context, tariffs, *args):
    tariff = tariffs[0]
    xpath = "x:validityConditions"
    validity_conditions = tariff.xpath(xpath, namespaces=NAMESPACE)
    if not validity_conditions:
        validity_conditions_sourceline = tariff.sourceline
        response_details = XMLViolationDetail(
            "violation",
            validity_conditions_sourceline,
            MESSAGE_OBSERVATION_TARIFF_VALIDITY_CONDITIONS_MISSING,
        )
        response = response_details.__list__()
        return response
    xpath = "x:ValidBetween"
    valid_between = validity_conditions[0].xpath(xpath, namespaces=NAMESPACE)
    if not valid_between:
        valid_between_sourceline = validity_conditions[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            valid_between_sourceline,
            MESSAGE_OBSERVATION_TARIFF_VALID_BETWEEN_MISSING,
        )
        response = response_details.__list__()
        return response
    xpath = "string(x:FromDate)"
    from_date = valid_between[0].xpath(xpath, namespaces=NAMESPACE)
    if not from_date:
        from_date_sourceline = valid_between[0].sourceline
        response_details = XMLViolationDetail(
            "violation",
            from_date_sourceline,
            MESSAGE_OBSERVATION_TARIFF_FROM_DATE_MISSING,
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
            xpath = "x:fareProducts"
            fare_products = fare_frame.xpath(xpath, namespaces=NAMESPACE)
            if not fare_products:
                sourceline = fare_frame.sourceline
                response_details = XMLViolationDetail(
                    "violation", sourceline, MESSAGE_OBSERVATION_FARE_PRODUCTS_MISSING
                )
                response = response_details.__list__()
                return response
            xpath = "x:PreassignedFareProduct"
            preassigned_fare_product = fare_products[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not preassigned_fare_product:
                sourceline_fare_product = fare_products[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_product,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "string(x:Name)"
            name = preassigned_fare_product[0].xpath(xpath, namespaces=NAMESPACE)
            if not name:
                sourceline_preassigned = preassigned_fare_product[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_preassigned,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_NAME_MISSING,
                )
                response = response_details.__list__()
                return response


def check_preassigned_fare_products_type_ref(context, preassigned_fare_products, *args):
    """
    Check if mandatory element is 'TypeOfFareProductRef' present in PreassignedFareProduct
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    preassigned_fare_product = preassigned_fare_products[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = preassigned_fare_product.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "x:TypeOfFareProductRef"
            type_of_fare_product = preassigned_fare_product.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not type_of_fare_product:
                sourceline_preassigned = preassigned_fare_product.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_preassigned,
                    MESSAGE_OBSERVATION_PREASSIGNED_TYPE_OF_FARE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_preassigned_fare_products_charging_type(
    context, preassigned_fare_products, *args
):
    """
    Check if mandatory element is 'ChargingMomentType' present in PreassignedFareProduct
    for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    preassigned_fare_product = preassigned_fare_products[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = preassigned_fare_product.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "string(x:ChargingMomentType)"
            charging_moment_type = preassigned_fare_product.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not charging_moment_type:
                sourceline_preassigned = preassigned_fare_product.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_preassigned,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_CHARGING_MISSING,
                )
                response = response_details.__list__()
                return response


def check_preassigned_validable_elements(context, preassigned_fare_products, *args):
    """
    Check if element 'validableElements' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    preassigned_fare_product = preassigned_fare_products[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = preassigned_fare_product.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "x:validableElements"
            validable_elements = preassigned_fare_product.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not validable_elements:
                sourceline_fare_frame = preassigned_fare_product.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_ELEMENTS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:ValidableElement"
            validable_element = validable_elements[0].xpath(xpath, namespaces=NAMESPACE)
            if not validable_element:
                sourceline_validable_element = validable_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_validable_element,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_ELEMENT_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:fareStructureElements"
            fare_structure_elements = validable_element[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not fare_structure_elements:
                sourceline_fare_structure = validable_element[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_structure,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_FARE_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:FareStructureElementRef"
            fare_structure_element_ref = fare_structure_elements[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not fare_structure_element_ref:
                sourceline_fare_structure_ref = fare_structure_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_structure_ref,
                    MESSAGE_OBSERVATION_PREASSIGNED_FARE_VALIDABLE_FARE_REF_MISSING,
                )
                response = response_details.__list__()
                return response


def check_access_right_elements(context, preassigned_fare_products, *args):
    """
    Check if mandatory element 'AccessRightInProduct' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    preassigned_fare_product = preassigned_fare_products[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = preassigned_fare_product.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "x:accessRightsInProduct"
            access_right = preassigned_fare_product.xpath(xpath, namespaces=NAMESPACE)
            if not access_right:
                sourceline_preassigned = preassigned_fare_product.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_preassigned,
                    MESSAGE_OBSERVATION_PREASSIGNED_ACCESS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:AccessRightInProduct/x:ValidableElementRef"
            validable_element_ref = access_right[0].xpath(xpath, namespaces=NAMESPACE)
            if not validable_element_ref:
                xpath = "x:AccessRightInProduct"
                child_access_right = access_right[0].xpath(xpath, namespaces=NAMESPACE)
                if not child_access_right:
                    sourceline_validable_element_ref = access_right[0].sourceline
                sourceline_validable_element_ref = child_access_right[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_validable_element_ref,
                    MESSAGE_OBSERVATION_PREASSIGNED_ACCESS_VALIDABLE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_product_type(context, preassigned_fare_products, *args):
    """
    Check if mandatory element 'ProductType'is missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    preassigned_fare_product = preassigned_fare_products[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = preassigned_fare_product.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "string(x:ProductType)"
            product_type = preassigned_fare_product.xpath(xpath, namespaces=NAMESPACE)
            if not product_type:
                sourceline_fare_frame = preassigned_fare_product.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_fare_frame,
                    MESSAGE_OBSERVATION_PREASSIGNED_PRODUCT_TYPE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_sales_offer_package(context, fare_frames, *args):
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
            xpath = "x:SalesOfferPackage"
            sales_offer_package = sales_offer_packages[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not sales_offer_package:
                sourceline_sales_offer_packages = sales_offer_packages[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_sales_offer_packages,
                    MESSAGE_OBSERVATION_SALES_OFFER_PACKAGE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_dist_assignments(context, sales_offer_packages, *args):
    """
    Check if mandatory salesOfferPackage.distributionAssignments elements missing for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    sales_offer_package = sales_offer_packages[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = sales_offer_package.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "x:distributionAssignments"
            distribution_assignments = sales_offer_package.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not distribution_assignments:
                sourceline_sales_offer_package = sales_offer_package.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_sales_offer_package,
                    MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENTS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:DistributionAssignment"
            distribution_assignment = distribution_assignments[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not distribution_assignment:
                sourceline_distribution_assignments = distribution_assignments[
                    0
                ].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_distribution_assignments,
                    MESSAGE_OBSERVATION_SALES_OFFER_ASSIGNMENT_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "string(x:DistributionChannelType)"
            distribution_type = distribution_assignment[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not distribution_type:
                sourceline_distribution_assignment = distribution_assignment[
                    0
                ].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_distribution_assignment,
                    MESSAGE_OBSERVATION_SALES_OFFER_DIST_CHANNEL_TYPE_MISSING,
                )
                response = response_details.__list__()
                return response


def check_payment_methods(context, distribution_assignments, *args):
    """
    Check if mandatory element 'PaymentMethods' is missing for DistributionAssignment in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    distribution_assignment = distribution_assignments[0]
    xpath = "../../../../x:TypeOfFrameRef"
    type_of_frame_refs = distribution_assignment.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "string(x:PaymentMethods)"
            payment_method = distribution_assignment.xpath(xpath, namespaces=NAMESPACE)
            if not payment_method:
                sourceline_distribution_assignment = distribution_assignment.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_distribution_assignment,
                    MESSAGE_OBSERVATION_SALES_OFFER_PAYMENT_METHODS_MISSING,
                )
                response = response_details.__list__()
                return response


def check_sale_offer_package_elements(context, sales_offer_packages, *args):
    """
    Check if mandatory element 'salesOfferPackageElements' or it's children missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    sales_offer_package = sales_offer_packages[0]
    xpath = "../../x:TypeOfFrameRef"
    type_of_frame_refs = sales_offer_package.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "x:salesOfferPackageElements"
            sales_offer_elements = sales_offer_package.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not sales_offer_elements:
                sourceline_sales_offer_package = sales_offer_package.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_sales_offer_package,
                    MESSAGE_OBSERVATION_SALES_OFFER_ELEMENTS_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:SalesOfferPackageElement"
            sales_offer_element = sales_offer_elements[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not sales_offer_element:
                sourceline_sales_package_elements = sales_offer_elements[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_sales_package_elements,
                    MESSAGE_OBSERVATION_SALES_OFFER_ELEMENT_MISSING,
                )
                response = response_details.__list__()
                return response
            xpath = "x:TypeOfTravelDocumentRef"
            type_of_travel_document_ref = sales_offer_element[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not type_of_travel_document_ref:
                sourceline_sales_offer_element = sales_offer_element[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_sales_offer_element,
                    MESSAGE_OBSERVATION_SALES_OFFER_TRAVEL_DOC_MISSING,
                )
                response = response_details.__list__()
                return response


def check_fare_product_ref(context, sales_offer_package_elements, *args):
    """
    Check if mandatory element 'PreassignedFareProductRef' is missing in
    salesOfferPackages for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    sales_offer_package_element = sales_offer_package_elements[0]
    xpath = "../../../../x:TypeOfFrameRef"
    type_of_frame_refs = sales_offer_package_element.xpath(xpath, namespaces=NAMESPACE)
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
            xpath = "x:PreassignedFareProductRef"
            preassigned_fare_product_ref = sales_offer_package_element.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not preassigned_fare_product_ref:
                sourceline_sales_offer_package_element = (
                    sales_offer_package_element.sourceline
                )
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_sales_offer_package_element,
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
                MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if FARE_STRUCTURE_ELEMENT_ACCESS_REF == type_of_fare_structure_element_ref_ref:
            xpath = "x:GenericParameterAssignment"
            generic_parameter = fare_structure_element.xpath(
                xpath, namespaces=NAMESPACE
            )
            if not generic_parameter:
                sourceline_generic_parameter = fare_structure_element.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_generic_parameter,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER,
                )
                response = response_details.__list__()
                return response
            xpath = "x:TypeOfAccessRightAssignmentRef"
            access_right_assignment = generic_parameter[0].xpath(
                xpath, namespaces=NAMESPACE
            )
            if not access_right_assignment:
                sourceline_access_right_assignment = generic_parameter[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_access_right_assignment,
                    MESSAGE_OBSERVATION_ACCESS_RIGHT_ASSIGNMENT,
                )
                response = response_details.__list__()
                return response


def check_validity_grouping_type_for_access(
    context, generic_parameter_assignments, *args
):
    """
    Checks if 'GenericParameterAssignment' has either 'ValidityParameterGroupingType'
    or 'ValidityParameterAssignmentType' elements within it when
    'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'
    """
    generic_parameter_assignment = generic_parameter_assignments[0]
    xpath = "../x:TypeOfFareStructureElementRef"
    type_of_fare_structure_element_ref = generic_parameter_assignment.xpath(
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
            MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    if FARE_STRUCTURE_ELEMENT_ACCESS_REF == type_of_fare_structure_element_ref_ref:
        xpath = "string(x:ValidityParameterGroupingType)"
        grouping_type = generic_parameter_assignment.xpath(xpath, namespaces=NAMESPACE)

        xpath = "string(x:ValidityParameterAssignmentType)"
        assignment_type = generic_parameter_assignment.xpath(
            xpath, namespaces=NAMESPACE
        )

        if not (grouping_type or assignment_type):
            sourceline_generic_parameter = generic_parameter_assignment.sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_generic_parameter,
                MESSAGE_OBSERVATION_VALIDITY_GROUPING_PARAMETER,
            )
            response = response_details.__list__()
            return response


def check_validity_parameter_for_access(context, generic_parameter_assignments, *args):
    """
    Checks if 'GenericParameterAssignment' has 'validityParameters' elements within it when
    'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'
    """
    generic_parameter_assignment = generic_parameter_assignments[0]
    xpath = "../x:TypeOfFareStructureElementRef"
    type_of_fare_structure_element_ref = generic_parameter_assignment.xpath(
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
            MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
        )
        response = response_details.__list__()
        return response
    if FARE_STRUCTURE_ELEMENT_ACCESS_REF == type_of_fare_structure_element_ref_ref:
        generic_parameter_assignment = generic_parameter_assignments[0]
        xpath = "x:validityParameters"
        validity_parameters = generic_parameter_assignment.xpath(
            xpath, namespaces=NAMESPACE
        )
        if not validity_parameters:
            sourceline_generic_parameter = generic_parameter_assignment.sourceline
            response_details = XMLViolationDetail(
                "violation",
                sourceline_generic_parameter,
                MESSAGE_OBSERVATION_VALIDITY_PARAMETER,
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
                MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
            )
            response = response_details.__list__()
            return response
        if (
            FARE_STRUCTURE_ELEMENT_ELIGIBILITY_REF
            == type_of_fare_structure_element_ref_ref
        ):
            generic_parameter = fare_structure_element.xpath(
                "x:GenericParameterAssignment", namespaces=NAMESPACE
            )
            if not generic_parameter:
                sourceline_generic_parameter = fare_structure_element.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_generic_parameter,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER,
                )
                response = response_details.__list__()
                return response
            limitations = generic_parameter[0].xpath(
                "x:limitations", namespaces=NAMESPACE
            )
            if not limitations:
                sourceline_limitations = generic_parameter[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_limitations,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATION,
                )
                response = response_details.__list__()
                return response
            xpath = "x:UserProfile"
            user_profile = limitations[0].xpath(xpath, namespaces=NAMESPACE)
            if not user_profile:
                sourceline_user_profile = limitations[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_user_profile,
                    MESSAGE_OBSERVATION_GENERIC_PARAMETER_LIMITATIONS_USER,
                )
                response = response_details.__list__()
                return response
            xpath = "string(x:Name)"
            user_profile_name = user_profile[0].xpath(xpath, namespaces=NAMESPACE)
            xpath = "string(x:UserType)"
            user_type = user_profile[0].xpath(xpath, namespaces=NAMESPACE)
            if not (user_profile_name and user_type):
                sourceline = user_profile[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline,
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
                MESSAGE_TYPE_OF_FARE_STRUCTURE_ELEMENT_REF_MISSING,
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
            xpath = "string(x:GenericParameterAssignment/x:limitations/x:FrequencyOfUse/x:FrequencyOfUseType)"
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


def check_composite_frame_valid_between(context, composite_frames, *args):
    """
    Check if ValidBetween and it's child are present in CompositeFrame
    """
    composite_frame = composite_frames[0]
    try:
        composite_frame_id = _extract_attribute(composite_frames, "id")
    except KeyError:
        sourceline = composite_frame.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING,
        )
        response = response_details.__list__()
        return response
    if TYPE_OF_FRAME_METADATA_SUBSTRING not in composite_frame_id:
        xpath = "x:ValidBetween"
        valid_between = composite_frame.xpath(xpath, namespaces=NAMESPACE)
        if not valid_between:
            source_line_valid_between = composite_frame.sourceline
            response_details = XMLViolationDetail(
                "violation",
                source_line_valid_between,
                MESSAGE_OBSERVATION_COMPOSITE_FRAME_VALID_BETWEEN_MISSING,
            )
            response = response_details.__list__()
            return response
        xpath = "string(x:FromDate)"
        from_date = valid_between[0].xpath(xpath, namespaces=NAMESPACE)
        if not from_date:
            source_line_from_date = valid_between[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                source_line_from_date,
                MESSAGE_OBSERVATION_COMPOSITE_FRAME_FROM_DATE,
            )
            response = response_details.__list__()
            return response


def check_resource_frame_organisation_elements(context, composite_frames, *args):
    """
    Check if mandatory element 'ResourceFrame' or it's child missing from CompositeFrame
    """
    composite_frame = composite_frames[0]
    try:
        composite_frame_id = _extract_attribute(composite_frames, "id")
    except KeyError:
        sourceline = composite_frame.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING,
        )
        response = response_details.__list__()
        return response
    if TYPE_OF_FRAME_METADATA_SUBSTRING not in composite_frame_id:
        xpath = "x:frames/x:ResourceFrame/x:organisations"
        organisations = composite_frame.xpath(xpath, namespaces=NAMESPACE)
        if not organisations:
            xpath = "x:frames/x:ResourceFrame"
            resource_frame = composite_frame.xpath(xpath, namespaces=NAMESPACE)
            if not resource_frame:
                xpath = "x:frames"
                frames = composite_frame.xpath(xpath, namespaces=NAMESPACE)
                source_line_resource_frame = frames[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    source_line_resource_frame,
                    MESSAGE_OBSERVATION_RESOURCE_FRAME_MISSING,
                )
                response = response_details.__list__()
                return response
            source_line_organisations = resource_frame[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                source_line_organisations,
                MESSAGE_OBSERVATION_RESOURCE_FRAME_ORG_MISSING,
            )
            response = response_details.__list__()
            return response
        xpath = "x:Operator"
        operators = organisations[0].xpath(xpath, namespaces=NAMESPACE)
        if not operators:
            source_line_operators = organisations[0].sourceline
            response_details = XMLViolationDetail(
                "violation",
                source_line_operators,
                MESSAGE_OBSERVATION_RESOURCE_FRAME_OPERATOR_MISSING,
            )
            response = response_details.__list__()
            return response
        for operator in operators:
            try:
                operator_id = _extract_attribute([operator], "id")
            except KeyError:
                sourceline_operator = operator.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_operator,
                    MESSAGE_OPERATORS_ID_MISSING,
                )
                response = response_details.__list__()
                return response
            if not (
                ORG_OPERATOR_ID_SUBSTRING in operator_id
                and len(operator_id) == LENGTH_OF_OPERATOR
            ):
                sourceline_operator = operator.sourceline
                response_details = XMLViolationDetail(
                    "violation", sourceline_operator, MESSAGE_OBSERVATION_OPERATOR_ID
                )
                response = response_details.__list__()
                return response
            xpath = "x:PublicCode"
            public_code = operator.xpath(xpath, namespaces=NAMESPACE)
            if not public_code:
                source_line_public_code = operator.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    source_line_public_code,
                    MESSAGE_OBSERVATION_RESOURCE_FRAME_PUBLIC_CODE_MISSING,
                )
                response = response_details.__list__()
                return response
            public_code_value = _extract_text(public_code)
            if len(public_code_value) != LENGTH_OF_PUBLIC_CODE:
                sourceline_public_code = public_code[0].sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    sourceline_public_code,
                    MESSAGE_OBSERVATION_PUBLIC_CODE_LENGTH,
                )
                response = response_details.__list__()
                return response


def check_resource_frame_operator_name(context, composite_frames, *args):
    """
    Check if mandatory element 'Name' is missing from organisations in ResourceFrame
    """
    composite_frame = composite_frames[0]
    try:
        composite_frame_id = _extract_attribute(composite_frames, "id")
    except KeyError:
        sourceline = composite_frame.sourceline
        response_details = XMLViolationDetail(
            "violation",
            sourceline,
            MESSAGE_OBSERVATION_COMPOSITE_FRAME_ID_MISSING,
        )
        response = response_details.__list__()
        return response
    if TYPE_OF_FRAME_METADATA_SUBSTRING not in composite_frame_id:
        xpath = "x:frames/x:ResourceFrame/x:organisations/x:Operator"
        operators = composite_frame.xpath(xpath, namespaces=NAMESPACE)
        for operator in operators:
            xpath = "string(x:Name)"
            name = operator.xpath(xpath, namespaces=NAMESPACE)
            if not name:
                source_line_name = operator.sourceline
                response_details = XMLViolationDetail(
                    "violation",
                    source_line_name,
                    MESSAGE_OBSERVATION_RESOURCE_FRAME_OPERATOR_NAME_MISSING,
                )
                response = response_details.__list__()
                return response
