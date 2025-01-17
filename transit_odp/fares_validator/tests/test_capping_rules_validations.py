import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    validate_cappeddiscountright_rules,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}
X_PATH = "//x:dataObjects/x:CompositeFrame"


def get_lxml_element(xpath, string_xml):
    doc = etree.fromstring(string_xml)
    elements = doc.xpath(xpath, namespaces=NAMESPACE)
    return elements


def test_capping_rule_name_present():
    """
    Test if mandatory element 'Name' is present for CappingRule
    """
    input_xml = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                        <Name>Fare products</Name>
                        <TypeOfFrameRef version="fxc:v1.0" ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP"/>
                        <fareProducts>
                            <CappedDiscountRight id="op:Cap:@trip" version="1.0">
                            <Name>Cap noc:FSYO</Name>
                            <cappingRules>
                                <CappingRule version="1.0" id="op:Tap_and_Cap_Day@flatFare_trip">
                                <Name>Tap and Cap Day</Name>
                                <CappingPeriod>day</CappingPeriod>
                                <ValidableElementRef version="1.0" ref="op:Pass@Flat_Single_adult@travel"/>
                                <GenericParameterAssignment version="1.0" id="Tap_and_Cap_Day@Flat_Single" order="1">
                                    <Name>limit a adult to 1 day</Name>
                                    <PreassignedFareProductRef version="1.0" ref="op:Pass@Flat_Single_adult"/>
                                    <limitations>
                                    <UserProfileRef version="1.0" ref="op:adult-0"/>
                                    </limitations>
                                    <TimeIntervalRef version="1.0" ref="op:Tariff@Tap-and_Cap_Day@1day"/>
                                </GenericParameterAssignment>
                                </CappingRule>
                            </cappingRules>
                            </CappedDiscountRight>
                        </fareProducts>
                    </FareFrame>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    composite_frames = get_lxml_element(X_PATH, input_xml)
    response = validate_cappeddiscountright_rules("", composite_frames)
    assert response is None


def test_capping_rule_name_not_present():
    """
    Test if mandatory element 'Name' is present for CappingRule
    """
    input_xml = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                        <Name>Fare products</Name>
                        <TypeOfFrameRef version="fxc:v1.0" ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP"/>
                        <fareProducts>
                            <CappedDiscountRight id="op:Cap:@trip" version="1.0">
                            <Name>Cap noc:FSYO</Name>
                            <cappingRules>
                                <CappingRule version="1.0" id="op:Tap_and_Cap_Day@flatFare_trip">
                                <CappingPeriod>day</CappingPeriod>
                                <ValidableElementRef version="1.0" ref="op:Pass@Flat_Single_adult@travel"/>
                                <GenericParameterAssignment version="1.0" id="Tap_and_Cap_Day@Flat_Single" order="1">
                                    <Name>limit a adult to 1 day</Name>
                                    <PreassignedFareProductRef version="1.0" ref="op:Pass@Flat_Single_adult"/>
                                    <limitations>
                                    <UserProfileRef version="1.0" ref="op:adult-0"/>
                                    </limitations>
                                    <TimeIntervalRef version="1.0" ref="op:Tariff@Tap-and_Cap_Day@1day"/>
                                </GenericParameterAssignment>
                                </CappingRule>
                            </cappingRules>
                            </CappedDiscountRight>
                        </fareProducts>
                    </FareFrame>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """
    EXPECTED_RESULT = [
        "violation",
        "10",
        "Mandatory element 'Name' within 'cappingRules.CappingRule' is missing",
    ]
    composite_frames = get_lxml_element(X_PATH, input_xml)
    print(f"composite_frames: {composite_frames}")
    response = validate_cappeddiscountright_rules("", composite_frames)
    assert response == EXPECTED_RESULT


def test_capping_rule_period_present():
    """
    Test if mandatory element 'Name' is present for CappingRule
    """
    input_xml = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                        <Name>Fare products</Name>
                        <TypeOfFrameRef version="fxc:v1.0" ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP"/>
                        <fareProducts>
                            <CappedDiscountRight id="op:Cap:@trip" version="1.0">
                            <Name>Cap noc:FSYO</Name>
                            <cappingRules>
                                <CappingRule version="1.0" id="op:Tap_and_Cap_Day@flatFare_trip">
                                <Name>Tap and Cap Day</Name>
                                <CappingPeriod>day</CappingPeriod>
                                <ValidableElementRef version="1.0" ref="op:Pass@Flat_Single_adult@travel"/>
                                <GenericParameterAssignment version="1.0" id="Tap_and_Cap_Day@Flat_Single" order="1">
                                    <Name>limit a adult to 1 day</Name>
                                    <PreassignedFareProductRef version="1.0" ref="op:Pass@Flat_Single_adult"/>
                                    <limitations>
                                    <UserProfileRef version="1.0" ref="op:adult-0"/>
                                    </limitations>
                                    <TimeIntervalRef version="1.0" ref="op:Tariff@Tap-and_Cap_Day@1day"/>
                                </GenericParameterAssignment>
                                </CappingRule>
                            </cappingRules>
                            </CappedDiscountRight>
                        </fareProducts>
                    </FareFrame>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """
    composite_frames = get_lxml_element(X_PATH, input_xml)
    print(f"composite_frames: {composite_frames}")
    response = validate_cappeddiscountright_rules("", composite_frames)
    assert response is None


def test_capping_rule_period_not_present():
    """
    Test if mandatory element 'Name' is present for CappingRule
    """
    input_xml = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                        <Name>Fare products</Name>
                        <TypeOfFrameRef version="fxc:v1.0" ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP"/>
                        <fareProducts>
                            <CappedDiscountRight id="op:Cap:@trip" version="1.0">
                            <Name>Cap noc:FSYO</Name>
                            <cappingRules>
                                <CappingRule version="1.0" id="op:Tap_and_Cap_Day@flatFare_trip">
                                <Name>Tap and Cap Day</Name>
                                <ValidableElementRef version="1.0" ref="op:Pass@Flat_Single_adult@travel"/>
                                <GenericParameterAssignment version="1.0" id="Tap_and_Cap_Day@Flat_Single" order="1">
                                    <Name>limit a adult to 1 day</Name>
                                    <PreassignedFareProductRef version="1.0" ref="op:Pass@Flat_Single_adult"/>
                                    <limitations>
                                    <UserProfileRef version="1.0" ref="op:adult-0"/>
                                    </limitations>
                                    <TimeIntervalRef version="1.0" ref="op:Tariff@Tap-and_Cap_Day@1day"/>
                                </GenericParameterAssignment>
                                </CappingRule>
                            </cappingRules>
                            </CappedDiscountRight>
                        </fareProducts>
                    </FareFrame>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """
    EXPECTED_RESULT = [
        "violation",
        "10",
        "Mandatory element 'CappingPeriod' within 'cappingRules.CappingRule' is missing",
    ]
    composite_frames = get_lxml_element(X_PATH, input_xml)
    print(f"composite_frames: {composite_frames}")
    response = validate_cappeddiscountright_rules("", composite_frames)
    print(f"response: {response}")
    assert response == EXPECTED_RESULT


def test_capping_rule_validableelementref_present():
    """
    Test if mandatory element 'Name' is present for CappingRule
    """
    input_xml = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                        <Name>Fare products</Name>
                        <TypeOfFrameRef version="fxc:v1.0" ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP"/>
                        <fareProducts>
                            <CappedDiscountRight id="op:Cap:@trip" version="1.0">
                            <Name>Cap noc:FSYO</Name>
                            <cappingRules>
                                <CappingRule version="1.0" id="op:Tap_and_Cap_Day@flatFare_trip">
                                <Name>Tap and Cap Day</Name>
                                <CappingPeriod>day</CappingPeriod>
                                <ValidableElementRef version="1.0" ref="op:Pass@Flat_Single_adult@travel"/>
                                <GenericParameterAssignment version="1.0" id="Tap_and_Cap_Day@Flat_Single" order="1">
                                    <Name>limit a adult to 1 day</Name>
                                    <PreassignedFareProductRef version="1.0" ref="op:Pass@Flat_Single_adult"/>
                                    <limitations>
                                    <UserProfileRef version="1.0" ref="op:adult-0"/>
                                    </limitations>
                                    <TimeIntervalRef version="1.0" ref="op:Tariff@Tap-and_Cap_Day@1day"/>
                                </GenericParameterAssignment>
                                </CappingRule>
                            </cappingRules>
                            </CappedDiscountRight>
                        </fareProducts>
                    </FareFrame>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """
    composite_frames = get_lxml_element(X_PATH, input_xml)
    print(f"composite_frames: {composite_frames}")
    response = validate_cappeddiscountright_rules("", composite_frames)
    assert response is None


def test_capping_rule_validableelementref_not_present():
    """
    Test if mandatory element 'Name' is present for CappingRule
    """
    input_xml = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                        <Name>Fare products</Name>
                        <TypeOfFrameRef version="fxc:v1.0" ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP"/>
                        <fareProducts>
                            <CappedDiscountRight id="op:Cap:@trip" version="1.0">
                            <Name>Cap noc:FSYO</Name>
                            <cappingRules>
                                <CappingRule version="1.0" id="op:Tap_and_Cap_Day@flatFare_trip">
                                <Name>Tap and Cap Day</Name>
                                <CappingPeriod>day</CappingPeriod>
                                <GenericParameterAssignment version="1.0" id="Tap_and_Cap_Day@Flat_Single" order="1">
                                    <Name>limit a adult to 1 day</Name>
                                    <PreassignedFareProductRef version="1.0" ref="op:Pass@Flat_Single_adult"/>
                                    <limitations>
                                    <UserProfileRef version="1.0" ref="op:adult-0"/>
                                    </limitations>
                                    <TimeIntervalRef version="1.0" ref="op:Tariff@Tap-and_Cap_Day@1day"/>
                                </GenericParameterAssignment>
                                </CappingRule>
                            </cappingRules>
                            </CappedDiscountRight>
                        </fareProducts>
                    </FareFrame>
                    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:FSYO_products@pass:op" responsibilitySetRef="op:tariffs">
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """
    EXPECTED_RESULT = [
        "violation",
        "10",
        "Mandatory element 'ValidableElementRef' within 'cappingRules.CappingRule' is missing",
    ]
    composite_frames = get_lxml_element(X_PATH, input_xml)
    print(f"composite_frames: {composite_frames}")
    response = validate_cappeddiscountright_rules("", composite_frames)
    print(f"response: {response}")
    assert response == EXPECTED_RESULT
