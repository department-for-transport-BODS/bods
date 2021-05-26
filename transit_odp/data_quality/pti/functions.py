import re
from datetime import datetime
from typing import List, Union

from dateutil import parser
from lxml import etree

from transit_odp.data_quality.pti.constants import BANK_HOLIDAYS, OPERATION_DAYS

PROHIBITED = r",[]{}^=@:;#$£?%+<>«»\/|~_¬"

ElementsOrStr = Union[List[etree.Element], List[str], str]


def _extract_text(elements, default=None):
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


def has_prohibited_chars(context, element):
    chars = _extract_text(element, "")
    return len([c for c in chars if c in PROHIBITED]) > 0


def contains_date(context, text):
    text = _extract_text(text, default="")
    for word in text.split():
        try:
            if word.isdigit():
                continue
            parser.parse(word)
        except parser.ParserError:
            pass
        else:
            return True
    return False


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


def is_member_of(context, element, *args):
    text = _extract_text(element, default="")
    return text in args


def today(context):
    now = datetime.now().date().isoformat()
    date = parser.parse(now)
    return date.timestamp()


def cast_to_date(context, date):
    """
    Casts a lxml date element to an int.
    """
    text = _extract_text(date)
    return parser.parse(text).timestamp()


def cast_to_bool(context, elements: ElementsOrStr):
    """
    Casts either a list of str, list of Elements or a str to a boolean
    """
    text = _extract_text(elements, default="false")
    return text == "true"


def strip(context, text):
    text = _extract_text(text, default="")
    return text.strip()


def regex(context, element, pattern):
    chars = _extract_text(element, "")
    return re.match(pattern, chars) is not None


def to_days(context, days, *args):
    """Returns number of days as number of seconds."""
    return days * 24 * 60 * 60.0


def validate_line_id(context, lines):
    """
    Validates that Line@id has the correct format.
    """
    line = lines[0]
    ns = {"x": line.nsmap.get(None)}

    xpath = "string(@id)"
    line_id = line.xpath(xpath, namespaces=ns)

    xpath = "string(//x:Operators/x:Operator/x:NationalOperatorCode)"
    noc = line.xpath(xpath, namespaces=ns)

    xpath = "string(../../x:ServiceCode)"
    service_code = line.xpath(xpath, namespaces=ns)

    xpath = "string(x:LineName)"
    line_name = line.xpath(xpath, namespaces=ns)
    line_name = line_name.replace(" ", "")

    expected_line_id = f"{noc}:{service_code}:{line_name}"
    return line_id.startswith(expected_line_id)


def has_unique_links(context, sections):
    section = sections[0]
    ns = {"x": section.nsmap.get(None)}
    links = section.xpath("x:RouteLink", namespaces=ns)
    xpath = "concat(string(x:From/x:StopPointRef),'-', string(x:To/x:StopPointRef))"
    refs = [link.xpath(xpath, namespaces=ns) for link in links]
    return len(refs) == len(set(refs))


def validate_run_time(context, timing_links):
    """
    Validates journey timings.
    """
    timing_link = timing_links[0]
    ns = {"x": timing_link.nsmap.get(None)}

    run_time = timing_link.xpath("string(x:RunTime)", namespaces=ns)
    journey_pattern_timing_link_ref = timing_link.xpath("string(@id)", namespaces=ns)

    xpath = (
        "//x:VehicleJourneyTimingLink"
        f"[x:JourneyPatternTimingLinkRef='{journey_pattern_timing_link_ref}']"
    )
    from_xpath = xpath + "/x:From"
    from_ = timing_link.xpath(from_xpath, namespaces=ns)
    to_xpath = xpath + "/x:To"
    to_ = timing_link.xpath(to_xpath, namespaces=ns)
    has_from_to = any([from_, to_])

    zero_run_time = run_time in ("", "PT0S", "PT0M")

    if not zero_run_time and has_from_to:
        return False

    return True


def validate_timing_link_stops(context, sections):
    """
    Validates that all links in a section are ordered coherently by
    stop point ref.
    """
    section = sections[0]
    ns = {"x": section.nsmap.get(None)}
    links = section.xpath("x:JourneyPatternTimingLink", namespaces=ns)

    prev_link = links[0]
    for curr_link in links[1:]:
        to_ = prev_link.xpath("string(x:To/x:StopPointRef)", namespaces=ns)
        from_ = curr_link.xpath("string(x:From/x:StopPointRef)", namespaces=ns)

        if from_ != to_:
            return False

        prev_link = curr_link

    return True


def validate_modification_date_time(context, roots):
    root = roots[0]
    modification_date = root.attrib.get("ModificationDateTime")
    creation_date = root.attrib.get("CreationDateTime")
    revision_number = root.attrib.get("RevisionNumber")

    if revision_number == "0":
        return modification_date == creation_date
    else:
        return creation_date < modification_date


def validate_bank_holidays(context, bank_holidays):
    bank_holiday = bank_holidays[0]
    ns = {"x": bank_holiday.nsmap.get(None)}
    children = bank_holiday.getchildren()
    local_name = "local-name()"

    holidays = []
    for element in children:
        if element.xpath(local_name, namespaces=ns) in OPERATION_DAYS:
            days = [el.xpath(local_name, namespaces=ns) for el in element.getchildren()]
            holidays += days

    # .getchildren() will return comments this filters out the comments
    holidays = [h for h in holidays if h]
    return sorted(BANK_HOLIDAYS) == sorted(holidays)
