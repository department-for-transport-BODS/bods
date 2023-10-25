from unittest.mock import Mock

import pytest
from dateutil import parser
from freezegun import freeze_time
from lxml import etree
from lxml.etree import Element

from transit_odp.data_quality.pti.functions import (
    cast_to_bool,
    cast_to_date,
    check_flexible_service_timing_status,
    contains_date,
    has_flexible_or_standard_service,
    has_flexible_service_classification,
    has_name,
    has_prohibited_chars,
    has_unregistered_service_codes,
    is_member_of,
    today,
)
from transit_odp.data_quality.pti.tests.constants import TXC_END, TXC_START


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="true")], True),
        ([Mock(spec=Element, text="false")], False),
        (Mock(spec=Element, text="true"), True),
        (Mock(spec=Element, text="false"), False),
        (["true"], True),
        (["false"], False),
        ("true", True),
        ("false", False),
        (Mock(spec=Element), False),
    ],
)
def test_cast_to_bool(value, expected):
    context = Mock()
    actual = cast_to_bool(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            [Mock(spec=Element, text="2015-01-01")],
            parser.parse("2015-01-01").timestamp(),
        ),
        (
            Mock(spec=Element, text="2015-01-01"),
            parser.parse("2015-01-01").timestamp(),
        ),
        ("2015-01-01", parser.parse("2015-01-01").timestamp()),
    ],
)
def test_cast_to_date(value, expected):
    context = Mock()
    actual = cast_to_date(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "list_items", "expected"),
    [
        ([Mock(spec=Element, text="other")], ("one", "two"), False),
        ([Mock(spec=Element, text="one")], ("one", "two"), True),
        (Mock(spec=Element, text="other"), ("one", "two"), False),
        (Mock(spec=Element, text="one"), ("one", "two"), True),
        ("other", ("one", "two"), False),
        ("one", ("one", "two"), True),
        ("", ("one", "two"), False),
        (Mock(spec=Element), ("one", "two"), False),
    ],
)
def test_is_member_of(value, list_items, expected):
    context = Mock()
    actual = is_member_of(context, value, *list_items)
    assert actual == expected


@freeze_time("2020-02-02")
def test_today():
    context = Mock()
    actual = today(context)
    assert actual == parser.parse("2020-02-02").timestamp()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="hello,world")], True),
        ([Mock(spec=Element, text="hello world")], False),
        (Mock(spec=Element, text="hello,world"), True),
        (Mock(spec=Element, text="false"), False),
        (["hello,world"], True),
        (["false"], False),
        ("hello,world", True),
        ("false", False),
        (Mock(spec=Element), False),
    ],
)
def test_has_prohibited_chars(value, expected):
    context = Mock()
    actual = has_prohibited_chars(context, value)
    assert actual == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ([Mock(spec=Element, text="world")], False),
        ([Mock(spec=Element, text="2020-12-01 world")], True),
        (Mock(spec=Element, text="hello,world"), False),
        (Mock(spec=Element, text="12-01 world"), True),
        (["hello,world"], False),
        (["01/08/21 hello world"], True),
        ("hello,world", False),
        ("01/08/21 hello world", True),
        ("15 hello world", False),
        (Mock(spec=Element), False),
    ],
)
def test_contains_date(value, expected):
    context = Mock()
    actual = contains_date(context, value)
    assert actual == expected


def test_has_name_false():
    context = Mock()
    s = TXC_START + "<Sunday />" + TXC_END
    doc = etree.fromstring(s.encode("utf-8"))
    sunday = doc.getchildren()
    actual = has_name(context, sunday, "Monday", "Tuesday")
    assert not actual


def test_has_name_false_not_list():
    context = Mock()
    s = TXC_START + "<Sunday />" + TXC_END
    doc = etree.fromstring(s.encode("utf-8"))
    sunday = doc.getchildren()[0]
    actual = has_name(context, sunday, "Monday", "Tuesday")
    assert not actual


def test_has_name_true():
    context = Mock()
    s = TXC_START + "<Sunday />" + TXC_END
    doc = etree.fromstring(s.encode("utf-8"))
    sunday = doc.getchildren()
    actual = has_name(context, sunday, "Sunday", "Monday")
    assert actual


def test_has_name_true_not_list():
    context = Mock()
    s = TXC_START + "<Sunday />" + TXC_END
    doc = etree.fromstring(s.encode("utf-8"))
    sunday = doc.getchildren()[0]
    actual = has_name(context, sunday, "Sunday", "Monday")
    assert actual


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (["PF0000459:134", "PF0000459:134"], False),
        (["PF0000459:134", "UZ000KBUS:11"], True),
        (["PF0000459:134"], True),
        (["UZ000KBUS:11"], True),
    ],
)
def test_has_unregistered_service_codes(value, expected):
    one_service = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceCode>{0}</ServiceCode>
            </Service>
        </Services>
    </TransXChange>
    """
    two_services = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <ServiceCode>{0}</ServiceCode>
            </Service>
            <Service>
                <ServiceCode>{1}</ServiceCode>
            </Service>
        </Services>
    </TransXChange>
    """
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    service_codes_length = len(value)
    if service_codes_length > 1:
        string_xml = two_services.format(*value)
    else:
        string_xml = one_service.format(*value)

    doc = etree.fromstring(string_xml)
    elements = doc.xpath("//x:Services", namespaces=NAMESPACE)
    actual = has_unregistered_service_codes("", elements)
    assert actual == expected


@pytest.mark.parametrize(
    ("flexible_classification", "flexible_service", "standard_service", "expected"),
    [
        (True, True, True, True),
        (True, True, False, True),
        (True, False, True, False),
        (True, False, False, False),
        (False, False, True, True),
        (False, False, False, False),
    ],
)
def test_has_flexible_or_standard_service(
    flexible_classification, flexible_service, standard_service, expected
):
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    flexible_classification_present = """
        <ServiceClassification>
            <Flexible/>
        </ServiceClassification>
    """
    flexible_service_present = """
        <FlexibleService>
            <FlexibleJourneyPattern id="jp_1">
                <BookingArrangements>
                    <Description>The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm</Description>
                    <Phone>
                        <TelNationalNumber>0345 234 3344</TelNationalNumber>
                    </Phone>
                    <AllBookingsTaken>true</AllBookingsTaken>
                </BookingArrangements>
            </FlexibleJourneyPattern>
        </FlexibleService>
    """
    standard_service_present = """
        <StandardService>
            <Origin>Putteridge High School</Origin>
            <Destination>Church Street</Destination>
            <JourneyPattern id="jp_2">
            <DestinationDisplay>Church Street</DestinationDisplay>
            <OperatorRef>tkt_oid</OperatorRef>
            <Direction>inbound</Direction>
            <RouteRef>rt_0000</RouteRef>
            <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
            </JourneyPattern>
        </StandardService>
    """
    service = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
		    <Service>
                {0}
                {1}
                {2}
            </Service>
        </Services>
    </TransXChange>
    """
    if flexible_classification:
        if flexible_service:
            string_xml = service.format(
                flexible_classification_present,
                flexible_service_present,
                standard_service,
            )
        else:
            string_xml = service.format(
                flexible_classification_present, "", standard_service
            )
    else:
        if standard_service:
            string_xml = service.format("", "", standard_service_present)
        else:
            string_xml = service.format("", "", "")

    doc = etree.fromstring(string_xml)
    elements = doc.xpath("//x:Service", namespaces=NAMESPACE)
    actual = has_flexible_or_standard_service("", elements)
    assert actual == expected


@pytest.mark.parametrize(
    ("service_classification", "flexible", "expected"),
    [
        (True, True, True),
        (True, False, False),
        (False, False, False),
    ],
)
def test_has_flexible_service_classification(
    service_classification, flexible, expected
):
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    service_classification_present = """
        <ServiceClassification>
        </ServiceClassification>
    """
    service_classification_flexible_present = """
        <ServiceClassification>
            <Flexible/>
        </ServiceClassification>
    """
    service = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
		    <Service>
                {0}
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <BookingArrangements>
                            <Description>The booking office is open for all advance booking Monday to Friday 8:30am – 6:30pm, Saturday 9am – 5pm</Description>
                            <Phone>
                                <TelNationalNumber>0345 234 3344</TelNationalNumber>
                            </Phone>
                            <AllBookingsTaken>true</AllBookingsTaken>
                        </BookingArrangements>
                    </FlexibleJourneyPattern>
			    </FlexibleService>
            </Service>
            <Service>
                <StandardService>
                    <Origin>Putteridge High School</Origin>
                    <Destination>Church Street</Destination>
                    <JourneyPattern id="jp_2">
                    <DestinationDisplay>Church Street</DestinationDisplay>
                    <OperatorRef>tkt_oid</OperatorRef>
                    <Direction>inbound</Direction>
                    <RouteRef>rt_0000</RouteRef>
                    <JourneyPatternSectionRefs>js_1</JourneyPatternSectionRefs>
                    </JourneyPattern>
                </StandardService>
            </Service>
        </Services>
    </TransXChange>
    """
    if service_classification:
        if flexible:
            string_xml = service.format(service_classification_flexible_present)
        else:
            string_xml = service.format(service_classification_present)
    else:
        string_xml = service

    doc = etree.fromstring(string_xml)
    elements = doc.xpath("//x:Service", namespaces=NAMESPACE)
    actual = has_flexible_service_classification("", elements)
    assert actual == expected


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["otherPoint", "otherPoint", "otherPoint"], True),
        (["otherPoint", "TXT", "otherPoint"], False),
        (["", "", ""], False),
        (["XYZ", "ABC", ""], False),
    ],
)
def test_check_flexible_service_timing_status(values, expected):
    NAMESPACE = {"x": "http://www.transxchange.org.uk/"}
    timing_status = """
    <TransXChange xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" CreationDateTime="2021-09-29T17:02:03" ModificationDateTime="2023-07-11T13:44:47" Modification="revise" RevisionNumber="130" FileName="552-FEAO552--FESX-Basildon-2023-07-23-B58_X10_Normal_V3_Exports-BODS_V1_1.xml" SchemaVersion="2.4" RegistrationDocument="false" xsi:schemaLocation="http://www.transxchange.org.uk/ http://www.transxchange.org.uk/schema/2.4/TransXChange_general.xsd">
        <Services>
            <Service>
                <FlexibleService>
                    <FlexibleJourneyPattern id="jp_1">
                        <StopPointsInSequence>
                            <FixedStopUsage SequenceNumber="1">
                                <StopPointRef>0600000102</StopPointRef>
                                <TimingStatus>{0}</TimingStatus>
                            </FixedStopUsage>
                            <FixedStopUsage SequenceNumber="2">
                                <StopPointRef>0600000101</StopPointRef>
                                <TimingStatus>{1}</TimingStatus>
                            </FixedStopUsage>
                            <FlexibleStopUsage>
                                <StopPointRef>270002700155</StopPointRef>
                            </FlexibleStopUsage>
                            <FixedStopUsage SequenceNumber="4">
                                <StopPointRef>0600000103</StopPointRef>
                                <TimingStatus>{2}</TimingStatus>
                            </FixedStopUsage>
                        </StopPointsInSequence>
                    </FlexibleJourneyPattern>
                </FlexibleService>
            </Service>
        </Services>
    </TransXChange>
    """
    string_xml = timing_status.format(*values)
    doc = etree.fromstring(string_xml)
    elements = doc.xpath(
        "//x:Service/x:FlexibleService/x:FlexibleJourneyPattern", namespaces=NAMESPACE
    )
    actual = check_flexible_service_timing_status("", elements)
    assert actual == expected
