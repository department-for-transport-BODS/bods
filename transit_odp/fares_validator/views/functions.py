from ..constants import (
    FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING,
    LENGTH_OF_OPERATOR,
    LENGTH_OF_PUBLIC_CODE,
    ORG_OPERATOR_ID_SUBSTRING,
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
    ns = {"x": element.nsmap.get(None)}
    xpath = "string(//x:tariffs/x:Tariff/x:timeIntervals/x:TimeInterval/x:Name)"
    result = element.xpath(xpath, namespaces=ns)
    if not result:
        return False
    return True


def is_time_intervals_present_in_tarrifs(context, fare_frames, *args):
    """
    Check if ProductType is dayPass or periodPass.
    If true, timeIntervals element should be present in tarrifs
    """
    fare_frame = fare_frames[0]
    ns = {"x": fare_frame.nsmap.get(None)}
    xpath = "string(//x:fareProducts/x:PreassignedFareProduct/x:ProductType)"
    product_type = fare_frame.xpath(xpath, namespaces=ns)
    if product_type in ["dayPass", "periodPass"]:
        is_time_intervals_tag_present = get_tariff_time_intervals(fare_frames)
        if is_time_intervals_tag_present:
            return True
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


def check_type_of_frame_ref_ref(context, type_of_frame_ref, *args):
    """
    Check if FareFrame TypeOfFrameRef has either UK_PI_FARE_PRODUCT or
    UK_PI_FARE_PRICE in it.
    """
    try:
        type_of_frame_ref_ref = _extract_attribute(type_of_frame_ref, "ref")
    except KeyError:
        return False
    for ref_value in FAREFRAME_TYPE_OF_FRAME_REF_SUBSTRING:
        if ref_value in type_of_frame_ref_ref:
            return True
    return False


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
    ns = {"x": fare_structure_element.nsmap.get(None)}
    xpath = "//x:FareStructureElement"
    all_fare_structure_elements = fare_structure_element.xpath(xpath, namespaces=ns)
    length_all_fare_structure_elements = len(all_fare_structure_elements)

    if length_all_fare_structure_elements > 2:
        for element in all_fare_structure_elements:
            try:
                type_of_fare_structure_element_ref = element.xpath(
                    "x:TypeOfFareStructureElementRef", namespaces=ns
                )
                type_of_fare_structure_element_ref_ref = _extract_attribute(
                    type_of_fare_structure_element_ref, "ref"
                )
                list_type_of_fare_structure_element_ref_ref.append(
                    type_of_fare_structure_element_ref_ref
                )
                type_of_access_right_assignment_ref = element.xpath(
                    "x:GenericParameterAssignment/x:TypeOfAccessRightAssignmentRef",
                    namespaces=ns,
                )
                type_of_access_right_assignment_ref_ref = _extract_attribute(
                    type_of_access_right_assignment_ref, "ref"
                )
                list_type_of_access_right_assignment_ref_ref.append(
                    type_of_access_right_assignment_ref_ref
                )

                access_index = list_type_of_fare_structure_element_ref_ref.index(
                    "fxc:access"
                )
                can_access_index = list_type_of_access_right_assignment_ref_ref.index(
                    "fxc:can_access"
                )
                eligibility_index = list_type_of_fare_structure_element_ref_ref.index(
                    "fxc:eligibility"
                )
                eligibile_index = list_type_of_access_right_assignment_ref_ref.index(
                    "fxc:eligible"
                )
                travel_conditions_index = (
                    list_type_of_fare_structure_element_ref_ref.index(
                        "fxc:travel_conditions"
                    )
                )
                condition_of_use_index = (
                    list_type_of_access_right_assignment_ref_ref.index(
                        "fxc:condition_of_use"
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


def check_public_code_length(context, public_code, *args):
    """
    Check if PublicCode is 4 characters long
    """
    public_code_value = _extract_text(public_code)
    if public_code_value is not None:
        if len(public_code_value) == LENGTH_OF_PUBLIC_CODE:
            return True
    return False
