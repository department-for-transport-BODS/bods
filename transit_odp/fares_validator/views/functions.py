from lxml import etree


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


def has_name(context, elements, *args):
    """
    Checks if elements are in the list of names.
    """
    if not isinstance(elements, list):
        elements = [elements]

    for el in elements:
        namespaces = {"x": el.nsmap.get(None)}
        local_name = el.xpath("local-name()", namespaces=namespaces)
        if local_name not in args:
            return False
    return True


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
