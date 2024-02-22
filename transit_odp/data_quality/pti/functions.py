import re
from datetime import datetime
from typing import List, Union

from dateutil import parser
from isoduration import DurationParsingException, parse_duration
from isoduration.types import TimeDuration
from lxml import etree

from transit_odp.data_quality.pti.constants import (
    BANK_HOLIDAYS,
    OPERATION_DAYS,
    OTHER_PUBLIC_HOLIDAYS,
    SCOTTISH_BANK_HOLIDAYS,
)
from transit_odp.naptan.models import StopPoint

PROHIBITED = r",[]{}^=@:;#$£?%+<>«»\/|~_¬"

ElementsOrStr = Union[List[etree.Element], List[str], str]

ZERO_TIME_DURATION = TimeDuration(hours=0, minutes=0, seconds=0)


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


def validate_run_time(context, timing_links):
    """
    Validates journey timings.
    """
    timing_link = timing_links[0]
    ns = {"x": timing_link.nsmap.get(None)}
    run_time = timing_link.xpath("string(x:RunTime)", namespaces=ns)
    try:
        time_duration = parse_duration(run_time).time
    except DurationParsingException:
        has_run_time = False
    else:
        has_run_time = not time_duration == ZERO_TIME_DURATION

    journey_pattern_timing_link_ref = timing_link.xpath("string(@id)", namespaces=ns)
    xpath = (
        "//x:VehicleJourney/x:VehicleJourneyTimingLink"
        f"[x:JourneyPatternTimingLinkRef='{journey_pattern_timing_link_ref}']"
    )

    vj_timing_link = timing_link.xpath(xpath, namespaces=ns)
    if has_run_time and len(vj_timing_link) == 0:
        return True
    elif has_run_time and vj_timing_link[0].xpath("x:From", namespaces=ns):
        return False
    elif has_run_time and vj_timing_link[0].xpath("x:To", namespaces=ns):
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

    # .getchildren() will return comments: this filters out the comments.
    # It also removes occurrences of OTHER_PUBLIC_HOLIDAYS of which there may be many or
    # none.
    holidays = [h for h in holidays if h and h not in OTHER_PUBLIC_HOLIDAYS]

    # duplicate check
    if sorted(list(set(holidays))) != sorted(holidays):
        return False

    # optional Scottish holiday check
    scottish_removed = list(set(holidays) - set(SCOTTISH_BANK_HOLIDAYS))
    return sorted(BANK_HOLIDAYS) == sorted(scottish_removed)


def check_service_group_validations(context, services):
    services = services[0]
    ns = {"x": services.nsmap.get(None)}
    service_list = services.xpath("x:Service", namespaces=ns)
    registered_code_regex = re.compile("[a-zA-Z]{2}\\d{7}:[a-zA-Z0-9]+$")
    unregistered_code_regex = re.compile("UZ[a-zA-Z0-9]{7}:[a-zA-Z0-9]+$")

    registered_standard_service = len(
        list(
            filter(
                lambda s: registered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                )
                and s.xpath("x:StandardService", namespaces=ns),
                service_list,
            )
        )
    )
    unregistered_services = len(
        list(
            filter(
                lambda s: unregistered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                ),
                service_list,
            )
        )
    )
    registered_flexible_service = len(
        list(
            filter(
                lambda s: registered_code_regex.match(
                    s.xpath("string(x:ServiceCode)", namespaces=ns)
                )
                and s.xpath("x:ServiceClassification/x:Flexible", namespaces=ns),
                service_list,
            )
        )
    )

    total_services = (
        registered_standard_service
        + registered_flexible_service
        + unregistered_services
    )

    # More than one services are allowed only when there is a registered flexible service.
    # If there is a registered standard service then no other service types should be present
    if total_services == 1 or (
        total_services > 1
        and registered_flexible_service == 1
        and registered_standard_service == 0
    ):
        return True

    return False


def has_flexible_or_standard_service(context, services):
    """
    If it is a non-flexible service (flexible service is not defined),
    then it should have a StandardService defined. If validation fails,
    then a validation issue should be recorded in validation report.
    """
    for service in services:
        ns = {"x": service.nsmap.get(None)}
        service_classification = service.xpath(
            "x:ServiceClassification/x:Flexible", namespaces=ns
        )

        if service_classification:
            flexible_service_list = service.xpath("x:FlexibleService", namespaces=ns)
            if flexible_service_list:
                return True
            return False
        else:
            standard_service_list = service.xpath("x:StandardService", namespaces=ns)
            if standard_service_list:
                return True
            else:
                return False


def has_flexible_service_classification(context, services):
    """
    Check when file has detected a flexible service (includes
    FlexibleService), it has ServiceClassification and Flexible elements.
    If the file also has a standard service, then return True.
    """
    for service in services:
        ns = {"x": service.nsmap.get(None)}
        flexible_service_list = service.xpath("x:FlexibleService", namespaces=ns)

        if not flexible_service_list:
            return True

        service_classification_list = service.xpath(
            "x:ServiceClassification", namespaces=ns
        )
        if not service_classification_list:
            return False

        for service_classification in service_classification_list:
            if service_classification.xpath("x:Flexible", namespaces=ns):
                return True

        return False


def check_flexible_service_timing_status(context, flexiblejourneypatterns):
    timing_status_value_list = []
    flexiblejourneypattern = flexiblejourneypatterns[0]
    ns = {"x": flexiblejourneypattern.nsmap.get(None)}
    stop_points_in_seq_list = flexiblejourneypattern.xpath(
        "x:StopPointsInSequence", namespaces=ns
    )
    for stop_points_in_seq in stop_points_in_seq_list:
        fixed_stop_usage_list = stop_points_in_seq.xpath(
            "x:FixedStopUsage", namespaces=ns
        )
        flexible_stop_usage_list = stop_points_in_seq.xpath(
            "x:FlexibleStopUsage", namespaces=ns
        )

        if len(fixed_stop_usage_list) > 0 and len(flexible_stop_usage_list) > 0:
            for fixed_stop_usage in fixed_stop_usage_list:
                timing_status_value_list.append(
                    _extract_text(
                        fixed_stop_usage.xpath("x:TimingStatus", namespaces=ns), ""
                    )
                )

    result = all(
        timing_status_value == "otherPoint"
        for timing_status_value in timing_status_value_list
    )
    return result


def check_flexible_service_stop_point_ref(context, flexiblejourneypatterns):
    atco_codes_list = []
    flexiblejourneypattern = flexiblejourneypatterns[0]
    ns = {"x": flexiblejourneypattern.nsmap.get(None)}
    stop_points_in_seq_list = flexiblejourneypattern.xpath(
        "x:StopPointsInSequence", namespaces=ns
    )
    stop_points_in_flexzone_list = flexiblejourneypattern.xpath(
        "x:FlexibleZones", namespaces=ns
    )
    atco_codes_list = list(
        set(
            get_stop_point_ref_list(stop_points_in_seq_list, ns)
            + get_stop_point_ref_list(stop_points_in_flexzone_list, ns)
        )
    )

    total_compliant = StopPoint.objects.filter(
        atco_code__in=atco_codes_list, bus_stop_type="FLX", stop_type="BCT"
    ).count()

    return total_compliant == len(atco_codes_list)


def get_stop_point_ref_list(stop_points, ns):
    stop_point_ref_list = []
    for flex_stop_point in stop_points:
        flexible_stop_usage_list = flex_stop_point.xpath(
            "x:FlexibleStopUsage", namespaces=ns
        )
        if len(flexible_stop_usage_list) > 0:
            for flexible_stop_usage in flexible_stop_usage_list:
                stop_point_ref_list.append(
                    _extract_text(
                        flexible_stop_usage.xpath("x:StopPointRef", namespaces=ns), ""
                    )
                )

    return stop_point_ref_list


def check_flexible_service_times(context, vehiclejourneys):
    """
    Check when FlexibleVehicleJourney is present, that FlexibleServiceTimes
    is also present at least once. If not present at all, then return False.
    """
    ns = {"x": vehiclejourneys[0].nsmap.get(None)}
    flexible_vehiclejourneys = vehiclejourneys[0].xpath(
        "x:FlexibleVehicleJourney", namespaces=ns
    )
    if flexible_vehiclejourneys:
        for flexible_journey in flexible_vehiclejourneys:
            flexible_service_times = flexible_journey.xpath(
                "x:FlexibleServiceTimes", namespaces=ns
            )
            if len(flexible_service_times) == 0:
                return False

            return True
