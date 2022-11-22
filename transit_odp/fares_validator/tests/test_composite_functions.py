import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    check_composite_frame_valid_between,
    check_resource_frame_operator_name,
    check_resource_frame_organisation_elements,
    check_value_of_type_of_frame_ref,
)


@pytest.mark.parametrize(
    ("valid_between", "from_date", "expected"),
    [
        (True, True, None),
        (
            False,
            False,
            [
                "violation",
                "4",
                "Mandatory element 'ValidBetween' within 'CompositeFrame' is missing",
            ],
        ),
        (
            True,
            False,
            [
                "violation",
                "6",
                "Mandatory element 'FromDate' within 'CompositeFrame.ValidBetween' is missing or empty",
            ],
        ),
    ],
)
def test_composite_frame_valid_between(valid_between, from_date, expected):
    """
    Test if ValidBetween and it's child are present in CompositeFrame
    """
    valid_between_with_child = """
    <ValidBetween>
        <FromDate>442914</FromDate>
    </ValidBetween>
    """

    valid_between_without_child = """
    <ValidBetween>
    </ValidBetween>
    """

    composite_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                {0}
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if valid_between:
        if from_date:
            xml = composite_frames.format(valid_between_with_child)
        else:
            xml = composite_frames.format(valid_between_without_child)
    else:
        xml = composite_frames.format("")

    netex_xml = etree.fromstring(xml)
    xpath = "//x:dataObjects/x:CompositeFrame"
    composite_frames = netex_xml.xpath(
        xpath, namespaces={"x": "http://www.netex.org.uk/netex"}
    )

    response = check_composite_frame_valid_between("", composite_frames)
    assert response == expected


@pytest.mark.parametrize(
    ("type_of_frame_ref", "type_of_frame_ref_ref_valid", "expected"),
    [
        (True, True, None),
        (
            True,
            False,
            [
                "violation",
                "6",
                "Attribute 'ref' of 'TypeOfFrameRef' in 'CompositeFrame' "
                "does not contain 'UK_PI_LINE_FARE_OFFER' or 'UK_PI_NETWORK_OFFER'",
            ],
        ),
        (
            False,
            False,
            [
                "violation",
                "6",
                "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
            ],
        ),
    ],
)
def test_value_of_type_of_frame_ref(
    type_of_frame_ref, type_of_frame_ref_ref_valid, expected
):
    """
    Test if TypeOfFrameRef has either UK_PI_LINE_FARE_OFFER or
    UK_PI_NETWORK_OFFER in it.
    """
    type_of_frame_ref_ref_contains_valid_ref = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_LINE_FARE_OFFER:FXCP" version="fxc:v1.0"/>
    """
    type_of_frame_ref_ref_contains_invalid_ref = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_NETWORK:FXCP" version="fxc:v1.0"/>
    """
    type_of_frame_ref_without_ref = """
    <TypeOfFrameRef />
    """

    composite_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                {0}
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref:
        if type_of_frame_ref_ref_valid:
            xml = composite_frames.format(type_of_frame_ref_ref_contains_valid_ref)
        else:
            xml = composite_frames.format(type_of_frame_ref_ref_contains_invalid_ref)
    else:
        xml = composite_frames.format(type_of_frame_ref_without_ref)

    netex_xml = etree.fromstring(xml)
    xpath = "//x:dataObjects/x:CompositeFrame"
    composite_frames = netex_xml.xpath(
        xpath, namespaces={"x": "http://www.netex.org.uk/netex"}
    )

    response = check_value_of_type_of_frame_ref("", composite_frames)
    assert response == expected


@pytest.mark.parametrize(
    (
        "organisations",
        "resource_frame",
        "operators",
        "operator_id_valid",
        "public_code",
        "public_code_value_present",
        "expected",
    ),
    [
        (True, True, True, True, True, True, None),
        (
            False,
            False,
            False,
            False,
            False,
            False,
            [
                "violation",
                "5",
                "Mandatory element 'ResourceFrame' missing from 'CompositeFrame'",
            ],
        ),
        (
            False,
            True,
            False,
            False,
            False,
            False,
            [
                "violation",
                "7",
                "Mandatory element 'organisations' within 'ResourceFrame' is missing",
            ],
        ),
        (
            True,
            True,
            False,
            False,
            False,
            False,
            [
                "violation",
                "8",
                "Mandatory element 'Operator' within 'ResourceFrame.organisations' is missing",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            False,
            False,
            [
                "violation",
                "9",
                "Mandatory element 'PublicCode' within 'ResourceFrame."
                "organisations.Operator' is missing",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            True,
            True,
            ["violation", "9", "'Operator' attribute 'id' format should be noc:xxxx"],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            False,
            ["violation", "9", "'Operator' attribute 'id' format should be noc:xxxx"],
        ),
        (
            True,
            True,
            True,
            True,
            True,
            False,
            ["violation", "10", "Element 'Public Code' should be 4 characters long"],
        ),
    ],
)
def test_resource_frame_organisation_elements(
    organisations,
    resource_frame,
    operators,
    operator_id_valid,
    public_code,
    public_code_value_present,
    expected,
):
    """
    Test if mandatory element 'ResourceFrame' or it's child missing from CompositeFrame
    """
    resource_frame_with_all_children_properties = """
    <ResourceFrame version="1.0" id="epd:UK:SPSV:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <organisations>
            <Operator version="1.0" id="noc:SPSV">
              <PublicCode>SPSV</PublicCode>
            </Operator>
        </organisations>
    </ResourceFrame>
    """

    resource_frame_without_public_code_value_present = """
    <ResourceFrame version="1.0" id="epd:UK:SPSV:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <organisations>
            <Operator version="1.0" id="noc:SPSV">
              <PublicCode>SV</PublicCode>
            </Operator>
        </organisations>
    </ResourceFrame>
    """

    resource_frame_without_public_code = """
    <ResourceFrame version="1.0" id="epd:UK:SPSV:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <organisations>
            <Operator version="1.0" id="noc:SPSV">
            </Operator>
        </organisations>
    </ResourceFrame>
    """

    resource_frame_without_operator_id_valid = """
    <ResourceFrame version="1.0" id="epd:UK:SPSV:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <organisations>
            <Operator version="1.0" id="atco:SPSV">
              <PublicCode>SPSV</PublicCode>
            </Operator>
        </organisations>
    </ResourceFrame>
    """

    resource_frame_without_operators = """
    <ResourceFrame version="1.0" id="epd:UK:SPSV:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
        <organisations>
        </organisations>
    </ResourceFrame>
    """

    resource_frame_without_organisations = """
    <ResourceFrame version="1.0" id="epd:UK:SPSV:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
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
        if organisations:
            if operators:
                if operator_id_valid:
                    if public_code:
                        if public_code_value_present:
                            xml = frames.format(
                                resource_frame_with_all_children_properties
                            )
                        else:
                            xml = frames.format(
                                resource_frame_without_public_code_value_present
                            )
                    else:
                        xml = frames.format(resource_frame_without_public_code)
                else:
                    xml = frames.format(resource_frame_without_operator_id_valid)
            else:
                xml = frames.format(resource_frame_without_operators)
        else:
            xml = frames.format(resource_frame_without_organisations)
    else:
        xml = frames.format("")

    netex_xml = etree.fromstring(xml)
    xpath = "//x:dataObjects/x:CompositeFrame"
    composite_frames = netex_xml.xpath(
        xpath, namespaces={"x": "http://www.netex.org.uk/netex"}
    )

    response = check_resource_frame_organisation_elements("", composite_frames)
    assert response == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (True, None),
        (
            False,
            [
                "violation",
                "8",
                "Mandatory element 'Name' within 'ResourceFrame.organisations.Operator' is missing or empty",
            ],
        ),
    ],
)
def test_resource_frame_operator_name(name, expected):
    """
    Test if mandatory element 'Name' is missing from organisations in ResourceFrame
    """
    name_present = """
    <Name>SPSV</Name>
    """

    operators = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <ResourceFrame version="1.0" id="epd:UK:SPSV:ResourceFrame_UK_PI_COMMON:op" dataSourceRef="op:src" responsibilitySetRef="network_data">
                        <organisations>
                            <Operator version="1.0" id="noc:SPSV">
                                {0}
                            </Operator>
                        </organisations>
                    </ResourceFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if name:
        xml = operators.format(name_present)
    else:
        xml = operators.format("")

    netex_xml = etree.fromstring(xml)
    xpath = "//x:dataObjects/x:CompositeFrame"
    composite_frames = netex_xml.xpath(
        xpath, namespaces={"x": "http://www.netex.org.uk/netex"}
    )

    response = check_resource_frame_operator_name("", composite_frames)
    assert response == expected
