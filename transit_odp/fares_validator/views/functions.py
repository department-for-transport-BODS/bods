from ..constants import (
    LENGTH_OF_OPERATOR,
    LENGTH_OF_PUBLIC_CODE,
    ORG_OPERATOR_ID_SUBSTRING,
    TYPE_OF_FRAME_REF_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_FRAME_SUBSTRING,
    TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING,
    FARE_STRUCTURE_ELEMENT_REF,
    TYPE_OF_ACCESS_RIGHT_REF,
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
    Checks if elements are in the list of names
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
    type_of_frame_ref = _extract_attribute(element, "id")
    if TYPE_OF_FRAME_REF_FARE_PRODUCT_SUBSTRING in type_of_frame_ref:
        element = element[0]
        ns = {"x": element.nsmap.get(None)}
        xpath = "string(//x:tariffs//x:Tariff//x:timeIntervals//x:TimeInterval//x:Name)"
        result = element.xpath(xpath, namespaces=ns)
        if not result:
            return False
        return True
    return True


def get_fare_structure_elements(element):
    """
    Checks if the fareStructureElements properties are present
    """
    element = element[0]
    ns = {"x": element.nsmap.get(None)}
    xpath = "string(..//x:timeIntervals)"
    time_intervals = element.xpath(xpath, namespaces=ns)
    xpath = "string(..//x:timeIntervals//x:TimeIntervalRef)"
    time_interval_ref = element.xpath(xpath, namespaces=ns)
    if time_intervals and time_interval_ref:
        return True
    return False


def get_generic_parameter_assignment_properties(element):
    """
    Checks if the fareStructureElements properties are present
    """
    element = element[0]
    ns = {"x": element.nsmap.get(None)}
    xpath = "string(..//..//..//x:tariffs//x:Tariff//x:fareStructureElements//x:FareStructureElement//x:GenericParameterAssignment//x:limitations//x:RoundTrip)"
    round_trip = element.xpath(xpath, namespaces=ns)
    xpath = "string(..//..//..//x:tariffs//x:Tariff//x:fareStructureElements//x:FareStructureElement//x:GenericParameterAssignment//x:limitations//x:RoundTrip//x:TripType)"
    trip_type = element.xpath(xpath, namespaces=ns)
    if round_trip and trip_type:
        return True
    return False


def is_time_intervals_present_in_tarrifs(context, fare_frames, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    ns = {"x": fare_frame.nsmap.get(None)}
    xpath = "string(//x:fareProducts//x:PreassignedFareProduct//x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=ns)
    if product_type in ["dayPass", "periodPass"]:
        return get_tariff_time_intervals(fare_frames)
    return True


def is_fare_structure_element_present(context, fare_structure_elements, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, FareStructureElement elements
    should be present in Tariff.FareStructureElements
    """
    try:
        ref = _extract_attribute(fare_structure_elements, "ref")
    except KeyError:
        return False
    fare_structure_element = fare_structure_elements[0]
    ns = {"x": fare_structure_element.nsmap.get(None)}
    xpath = "string(..//..//..//..//..//x:fareProducts//x:PreassignedFareProduct//x:ProductType)"
    product_type = fare_structure_element.xpath(xpath, namespaces=ns)
    if product_type in ["dayPass", "periodPass"]:
        if FARE_STRUCTURE_ELEMENT_REF == ref:
            return get_fare_structure_elements(fare_structure_elements)
        return False
    return True


def is_generic_parameter_limitions_present(context, element, *args):
    """
    Check if ProductType is singleTrip, dayReturnTrip, periodReturnTrip.
    If true, FareStructureElement.GenericParameterAssignment elements should be present in Tariff.FareStructureElements
    """
    product_type = _extract_text(element)
    if product_type in ["singleTrip", "dayReturnTrip", "periodReturnTrip"]:
        return get_generic_parameter_assignment_properties(element)
    return False


def check_placement_validity_parameters(context, element, *args):
    """
    Check for validityParameters.
    It should either be nested within GenericParameterAssignment.ValidityParameterGroupingType
    or GenericParameterAssignment.ValidityParameterAssignmentType",
    """
    try:
        access_right_assignment_ref = _extract_attribute(element, "ref")
    except KeyError:
        return False
    if TYPE_OF_ACCESS_RIGHT_REF == access_right_assignment_ref:
        element = element[0]
        ns = {"x": element.nsmap.get(None)}
        xpath = "string(..//x:ValidityParameterGroupingType//x:validityParameters)"
        in_grouping_type = element.xpath(xpath, namespaces=ns)
        xpath = "string(..//x:ValidityParameterAssignmentType//x:validityParameters)"
        in_assignment_type = element.xpath(xpath, namespaces=ns)
        if in_grouping_type or in_assignment_type:
            return True
        return False
    return True


def is_fare_zones_present_in_fare_frame(context, fare_zones, *args):
    """
    Check if fareZones is present in FareFrame.
    If true, then fareZones properties should be present
    """
    try:
        ref = _extract_attribute(fare_zones, "ref")
    except KeyError:
        return False
    if TYPE_OF_FRAME_REF_FARE_FRAME_SUBSTRING in ref:
        ns = {"x": fare_zones[0].nsmap.get(None)}
        xpath = "string(..//x:fareZones)"
        is_fare_zones = fare_zones[0].xpath(xpath, namespaces=ns)
        if is_fare_zones:
            xpath = "string(..//x:fareZones//x:FareZone)"
            for fare_zone in fare_zones:
                is_fare_zone = fare_zone.xpath(xpath, namespaces=ns)
                if is_fare_zone:
                    xpath = "string(..//x:fareZones//x:FareZone//x:Name)"
                    is_fare_zone_name = fare_zone.xpath(xpath, namespaces=ns)
                    xpath = "string(..//x:fareZones//x:FareZone//x:members)"
                    is_fare_zone_members = fare_zone.xpath(xpath, namespaces=ns)
                    xpath = "string(..//x:fareZones//x:FareZone//x:members//x:ScheduledStopPointRef)"
                    is_fare_zone_members_stop_ref = fare_zone.xpath(
                        xpath, namespaces=ns
                    )
                    if (
                        is_fare_zone_name
                        and is_fare_zone_members
                        and is_fare_zone_members_stop_ref
                    ):
                        return True
                    return False
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
