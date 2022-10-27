from ..constants import (
    LENGTH_OF_OPERATOR,
    LENGTH_OF_PUBLIC_CODE,
    ORG_OPERATOR_ID_SUBSTRING,
    TYPE_OF_FRAME_REF_SUBSTRING,
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
