import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    check_fare_frame_type_of_frame_ref_present_fare_price,
    check_fare_frame_type_of_frame_ref_present_fare_product,
    check_resource_frame_type_of_frame_ref_present,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}
RESOURCE_FRAME_X_PATH = "//x:dataObjects/x:CompositeFrame"
FARE_FRAME_X_PATH = "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame"


def get_lxml_element(xpath, string_xml):
    doc = etree.fromstring(string_xml)
    elements = doc.xpath(xpath, namespaces=NAMESPACE)
    return elements


@pytest.mark.parametrize(
    (
        "fare_frame",
        "fare_frame_valid_id",
        "type_of_frame_ref",
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "expected",
    ),
    [
        (True, True, True, True, True, None),
        (True, False, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            False,
            [
                "violation",
                "7",
                "Mandatory element 'TypeOfFrameRef' is missing from 'FareFrame' - UK_PI_FARE_PRICE",
            ],
        ),
        (True, True, True, False, False, ""),
        (
            True,
            True,
            True,
            True,
            False,
            [
                "violation",
                "8",
                "Attribute 'ref' of element 'TypeOfFrameRef' does not contain 'UK_PI_FARE_PRICE'",
            ],
        ),
    ],
)
def test_fare_frame_type_of_frame_ref_present_fare_price(
    fare_frame,
    fare_frame_valid_id,
    type_of_frame_ref,
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    expected,
):
    """
    Test if mandatory element 'TypeOfFrameRef' and
    'UK_PI_FARE_PRICE' ref is present
    """
    fare_frame_with_all_properties = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRICE:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRICE:FXCP" version="fxc:v1.0"/>
    </FareFrame>
    """

    fare_frame_without_valid_type_of_frame_ref_ref = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRICE:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame:FXCP" version="fxc:v1.0"/>
    </FareFrame>
    """

    fare_frame_without_type_of_frame_ref_ref = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRICE:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
        <TypeOfFrameRef version="fxc:v1.0"/>
    </FareFrame>
    """

    fare_frame_without_type_of_frame_ref = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRICE:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
    </FareFrame>
    """

    fare_frame_without_valid_id = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if fare_frame:
        if fare_frame_valid_id:
            if type_of_frame_ref:
                if type_of_frame_ref_ref_present:
                    if type_of_frame_ref_ref_valid:
                        xml = frames.format(fare_frame_with_all_properties)
                    else:
                        xml = frames.format(
                            fare_frame_without_valid_type_of_frame_ref_ref
                        )
                else:
                    xml = frames.format(fare_frame_without_type_of_frame_ref_ref)
            else:
                xml = frames.format(fare_frame_without_type_of_frame_ref)
        else:
            xml = frames.format(fare_frame_without_valid_id)
    else:
        xml = frames.format("")

    frames = get_lxml_element(FARE_FRAME_X_PATH, xml)
    response = check_fare_frame_type_of_frame_ref_present_fare_price("", frames)
    assert response == expected


@pytest.mark.parametrize(
    (
        "fare_frame",
        "fare_frame_valid_id",
        "type_of_frame_ref",
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "expected",
    ),
    [
        (True, True, True, True, True, None),
        (True, False, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            False,
            [
                "violation",
                "7",
                "Mandatory element 'TypeOfFrameRef' is missing from 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (True, True, True, False, False, ""),
        (
            True,
            True,
            True,
            True,
            False,
            [
                "violation",
                "8",
                "Attribute 'ref' of element 'TypeOfFrameRef' does not contain 'UK_PI_FARE_PRODUCT'",
            ],
        ),
    ],
)
def test_fare_frame_type_of_frame_ref_present_fare_product(
    fare_frame,
    fare_frame_valid_id,
    type_of_frame_ref,
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    expected,
):
    """
    Test if mandatory element 'TypeOfFrameRef'
    and 'UK_PI_FARE_PRODUCT' ref is present
    """
    fare_frame_with_all_properties = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRODUCT:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0"/>
    </FareFrame>
    """

    fare_frame_without_valid_type_of_frame_ref_ref = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRODUCT:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame:FXCP" version="fxc:v1.0"/>
    </FareFrame>
    """

    fare_frame_without_type_of_frame_ref_ref = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRODUCT:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
        <TypeOfFrameRef version="fxc:v1.0"/>
    </FareFrame>
    """

    fare_frame_without_type_of_frame_ref = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame_UK_PI_FARE_PRODUCT:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
    </FareFrame>
    """

    fare_frame_without_valid_id = """
    <FareFrame version="1.0" id="epd:UK:LNUD:FareFrame:LNUD:PC0005248:1:152@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if fare_frame:
        if fare_frame_valid_id:
            if type_of_frame_ref:
                if type_of_frame_ref_ref_present:
                    if type_of_frame_ref_ref_valid:
                        xml = frames.format(fare_frame_with_all_properties)
                    else:
                        xml = frames.format(
                            fare_frame_without_valid_type_of_frame_ref_ref
                        )
                else:
                    xml = frames.format(fare_frame_without_type_of_frame_ref_ref)
            else:
                xml = frames.format(fare_frame_without_type_of_frame_ref)
        else:
            xml = frames.format(fare_frame_without_valid_id)
    else:
        xml = frames.format("")

    frames = get_lxml_element(FARE_FRAME_X_PATH, xml)
    response = check_fare_frame_type_of_frame_ref_present_fare_product("", frames)
    assert response == expected


@pytest.mark.parametrize(
    (
        "resource_frame",
        "resource_frame_valid_id",
        "type_of_frame_ref",
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "expected",
    ),
    [
        (True, True, True, True, True, None),
        (True, False, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            False,
            [
                "violation",
                "7",
                "Mandatory element 'TypeOfFrameRef' is missing from 'ResourceFrame' - UK_PI_COMMON",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            [
                "violation",
                "8",
                "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            False,
            [
                "violation",
                "8",
                "Attribute 'ref' of element 'TypeOfFrameRef' does not contain 'UK_PI_COMMON'",
            ],
        ),
    ],
)
def test_resource_frame_type_of_frame_ref_present(
    resource_frame,
    resource_frame_valid_id,
    type_of_frame_ref,
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    expected,
):
    """
    Test if mandatory element 'TypeOfFrameRef' is present in 'ResourceFrame'
    and 'UK_PI_COMMON' ref is present
    """
    resource_frame_with_all_properties = """
    <ResourceFrame version="1.0" id="epd:UK:LNUD:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_COMMON:FXCP" version="fxc:v1.0"/>
    </ResourceFrame>
    """

    resource_frame_without_valid_type_frame_ref_ref = """
    <ResourceFrame version="1.0" id="epd:UK:LNUD:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame:FXCP" version="fxc:v1.0"/>
    </ResourceFrame>
    """

    resource_frame_without_type_frame_ref_ref = """
    <ResourceFrame version="1.0" id="epd:UK:LNUD:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <TypeOfFrameRef version="fxc:v1.0"/>
    </ResourceFrame>
    """

    resource_frame_without_type_frame_ref = """
    <ResourceFrame version="1.0" id="epd:UK:LNUD:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
    </ResourceFrame>
    """

    resource_frame_without_valid_id = """
    <ResourceFrame version="1.0" id="epd:UK:LNUD:ResourceFrame:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
    </ResourceFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if resource_frame:
        if resource_frame_valid_id:
            if type_of_frame_ref:
                if type_of_frame_ref_ref_present:
                    if type_of_frame_ref_ref_valid:
                        xml = frames.format(resource_frame_with_all_properties)
                    else:
                        xml = frames.format(
                            resource_frame_without_valid_type_frame_ref_ref
                        )
                else:
                    xml = frames.format(resource_frame_without_type_frame_ref_ref)
            else:
                xml = frames.format(resource_frame_without_type_frame_ref)
        else:
            xml = frames.format(resource_frame_without_valid_id)
    else:
        xml = frames.format("")

    frames = get_lxml_element(RESOURCE_FRAME_X_PATH, xml)
    response = check_resource_frame_type_of_frame_ref_present("", frames)
    assert response == expected
