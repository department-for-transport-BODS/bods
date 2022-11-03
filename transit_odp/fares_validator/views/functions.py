from ..constants import (
    FARE_STRUCTURE_ELEMENT_REF,
    FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING,
    LENGTH_OF_OPERATOR,
    LENGTH_OF_PUBLIC_CODE,
    NAMESPACE,
    ORG_OPERATOR_ID_SUBSTRING,
    STOP_POINT_ID_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_ZONES_SUBSTRING,
    TYPE_OF_FRAME_REF_SUBSTRING,
    TYPE_OF_TARIFF_REF_SUBSTRING,
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
    Checks if the FareStructureElement.GenericParameterAssignment properties are present
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
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
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
    If true, FareStructureElement.GenericParameterAssignment elements
    should be present in Tariff.FareStructureElements
    """
    fare_frame = fare_frames[0]
    xpath = "string(x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=NAMESPACE)
    if product_type in ["singleTrip", "dayReturnTrip", "periodReturnTrip"]:
        return get_generic_parameter_assignment_properties(fare_frame)
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


def check_value_of_type_of_frame_ref(context, data_objects, *args):
    """
    Check if TypeOfFrameRef has either UK_PI_LINE_FARE_OFFER or
    UK_PI_NETWORK_OFFER in it.
    """
    data_object = data_objects[0]
    xpath = "x:CompositeFrame"
    composite_frames = data_object.xpath(xpath, namespaces=NAMESPACE)
    for composite_frame in composite_frames:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = composite_frame.xpath(xpath, namespaces=NAMESPACE)
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            return False
        for ref_value in TYPE_OF_FRAME_REF_SUBSTRING:
            if ref_value in type_of_frame_ref_ref:
                return True
    return False


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
    Check if ServiceFrame is present in FareFrame.
    If true, TypeOfFrameRef should include UK_PI_NETWORK
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
    Check if ServiceFrame is present in FareFrame,
    corresponding Line properties should be present
    """
    if lines:
        xpath = "x:Line"
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
    Check if ServiceFrame is present in FareFrame,
    it's other properties should be present
    """
    if schedule_stop_points:
        xpath = "x:ScheduledStopPoint"
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


def check_type_of_frame_ref_ref(context, composite_frames, *args):
    """
    Check if FareFrame TypeOfFrameRef has either UK_PI_FARE_PRODUCT or
    UK_PI_FARE_PRICE in it.
    """
    composite_frame = composite_frames[0]
    xpath = "//x:frames/x:FareFrame"
    fare_frames = composite_frame.xpath(xpath, namespaces=NAMESPACE)
    for fare_frame in fare_frames:
        xpath = "x:TypeOfFrameRef"
        type_of_frame_ref = fare_frame.xpath(xpath, namespaces=NAMESPACE)
        try:
            type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
        except KeyError:
            return False
        for ref_value in FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING:
            if ref_value in type_of_frame_ref_ref:
                return True


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
    result = False

    fare_structure_element = fare_structure_elements[0]
    xpath = "//x:FareStructureElement"
    all_fare_structure_elements = fare_structure_element.xpath(
        xpath, namespaces=NAMESPACE
    )
    length_all_fare_structure_elements = len(all_fare_structure_elements)

    if length_all_fare_structure_elements > 2:
        for element in all_fare_structure_elements:
            try:
                type_of_fare_structure_element_ref = element.xpath(
                    "x:TypeOfFareStructureElementRef", namespaces=NAMESPACE
                )
                type_of_fare_structure_element_ref_ref = _extract_attribute(
                    type_of_fare_structure_element_ref, "ref"
                )
                list_type_of_fare_structure_element_ref_ref.append(
                    type_of_fare_structure_element_ref_ref
                )
                type_of_access_right_assignment_ref = element.xpath(
                    "x:GenericParameterAssignment/x:TypeOfAccessRightAssignmentRef",
                    namespaces=NAMESPACE,
                )
                type_of_access_right_assignment_ref_ref = _extract_attribute(
                    type_of_access_right_assignment_ref, "ref"
                )
                list_type_of_access_right_assignment_ref_ref.append(
                    type_of_access_right_assignment_ref_ref
                )

                access_index = list_type_of_fare_structure_element_ref_ref.index(
                    "fxc:access"  # Move to constants
                )
                can_access_index = list_type_of_access_right_assignment_ref_ref.index(
                    "fxc:can_access"  # Move to constants
                )
                eligibility_index = list_type_of_fare_structure_element_ref_ref.index(
                    "fxc:eligibility"  # Move to constants
                )
                eligibile_index = list_type_of_access_right_assignment_ref_ref.index(
                    "fxc:eligible"  # Move to constants
                )
                travel_conditions_index = (
                    list_type_of_fare_structure_element_ref_ref.index(
                        "fxc:travel_conditions"  # Move to constants
                    )
                )
                condition_of_use_index = (
                    list_type_of_access_right_assignment_ref_ref.index(
                        "fxc:condition_of_use"  # Move to constants
                    )
                )

                # Compare indexes
                if (
                    access_index == can_access_index
                    and eligibility_index == eligibile_index
                    and travel_conditions_index == condition_of_use_index
                ):
                    result = True
            except ValueError:
                result = False
    return result


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
        if "fxc:access" in type_of_fare_structure_element_ref_ref:
            # Move fxc:access to constants
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
        if "fxc:eligibility" in type_of_fare_structure_element_ref_ref:
            # Move fxc:eligibility to constants
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
