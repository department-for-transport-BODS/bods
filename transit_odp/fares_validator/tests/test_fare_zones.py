import pytest

from transit_odp.fares_validator.views.functions import (is_fare_zones_present_in_fare_frame, is_name_present_in_fare_frame, is_members_scheduled_point_ref_present_in_fare_frame)
from lxml import etree

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}

MISSING_FARE_ZONES_PASS_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETWORK:FXCP" version="fxc:v1.0" />
      <FareZone id="fs@0476" version="1.0">
        <Name>Sheffield Interchange</Name>
        <members>
          <ScheduledStopPointRef ref="atco:370010134" version="any">Sheffield Interchange</ScheduledStopPointRef>
          <ScheduledStopPointRef ref="atco:370022831" version="any">FS1</ScheduledStopPointRef>
        </members>
      </FareZone>
      <FareZone id="fs@0001" version="1.0">
        <Name>12 o'clock court</Name>
        <members>
          <ScheduledStopPointRef ref="atco:370023485" version="any">12 O Clock Court</ScheduledStopPointRef>
        </members>
      </FareZone>
  </FareFrame>
  </PublicationDelivery>"""

FARE_ZONES_PASS_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETWORK:FXCP" version="fxc:v1.0" />
    <fareZones>
      <FareZone id="fs@0476" version="1.0">
        <Name>Sheffield Interchange</Name>
        <members>
          <ScheduledStopPointRef ref="atco:370010134" version="any">Sheffield Interchange</ScheduledStopPointRef>
          <ScheduledStopPointRef ref="atco:370022831" version="any">FS1</ScheduledStopPointRef>
        </members>
      </FareZone>
      <FareZone id="fs@0001" version="1.0">
        <Name>12 o'clock court</Name>
        <members>
          <ScheduledStopPointRef ref="atco:370023485" version="any">12 O Clock Court</ScheduledStopPointRef>
        </members>
      </FareZone>
    </fareZones>
  </FareFrame>
  </PublicationDelivery>"""

FARE_ZONES_FAIL_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETWORK:FXCP" version="fxc:v1.0" />
    <fareZones>
    </fareZones>
  </FareFrame>
  </PublicationDelivery>"""

FARE_ZONES_INCORRECT_REF ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETW:FXCP" version="fxc:v1.0" />
    <fareZones>
    </fareZones>
  </FareFrame>
  </PublicationDelivery>"""

FARE_ZONES_MISSING_REF ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    <TypeOfFrameRef version="fxc:v1.0" />
    <fareZones>
    <FareZone id="fs@0476" version="1.0">
        <Name>Sheffield Interchange</Name>
      </FareZone>
    </fareZones>
  </FareFrame>
  </PublicationDelivery>"""

FARE_ZONE_MISSING_NAME_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETWORK:FXCP" version="fxc:v1.0" />
    <fareZones>
      <FareZone id="fs@0476" version="1.0">
        <Name>Sheffield Interchange</Name>
        <members>
          <ScheduledStopPointRef ref="atco:370010134" version="any">Sheffield Interchange</ScheduledStopPointRef>
          <ScheduledStopPointRef ref="atco:370022831" version="any">FS1</ScheduledStopPointRef>
        </members>
      </FareZone>
      <FareZone id="fs@0001" version="1.0">
        <members>
          <ScheduledStopPointRef ref="atco:370023485" version="any">12 O Clock Court</ScheduledStopPointRef>
        </members>
      </FareZone>
    </fareZones>
  </FareFrame>
  </PublicationDelivery>"""

def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:fareZones"
    fare_zones = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_zones

def test_missing_fare_zones():
    expected = None
    fare_zones = get_lxml_element(MISSING_FARE_ZONES_PASS_XML)
    result = is_fare_zones_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_fare_zones_pass():
    expected = None
    doc = etree.fromstring(FARE_ZONES_PASS_XML)
    xpath = "//x:fareZones"
    fare_zones = doc.xpath(xpath, namespaces=NAMESPACE)
    result = is_fare_zones_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_missing_fare_zone():
    expected = ['violation', '4', "Element 'FareZone' is missing within 'fareZones'"]
    fare_zones = get_lxml_element(FARE_ZONES_FAIL_XML)
    result = is_fare_zones_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_incorrect_fare_zones_ref():
    expected = ['violation', '3', "Mandatory element 'TypeOfFrameRef' is missing or 'ref' value does not contain 'UK_PI_FARE_NETWORK'"]
    fare_zones = get_lxml_element(FARE_ZONES_INCORRECT_REF)
    result = is_fare_zones_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_missing_fare_zones_ref():
    expected = ['violation', '3', "Attribute 'ref' of element 'TypeOfFrameRef' is missing"]
    fare_zones = get_lxml_element(FARE_ZONES_MISSING_REF)
    result = is_fare_zones_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_fare_zone_name_pass():
    expected = None
    fare_zones = get_lxml_element(FARE_ZONES_PASS_XML)
    result = is_name_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_missing_fare_zone_name():
    expected = ['violation', '12', "Element 'Name' is missing or empty within the element 'FareZone'"]
    fare_zones = get_lxml_element(FARE_ZONE_MISSING_NAME_XML)
    result = is_name_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_fare_zone_members_pass():
    expected = None
    fare_zones = get_lxml_element(FARE_ZONE_MISSING_NAME_XML)
    result = is_members_scheduled_point_ref_present_in_fare_frame("context", fare_zones)
    assert result == expected

def test_missing_fare_zone_members():
    expected = ['violation', '5', "Element 'members' is missing within the element 'FareZone'"]
    fare_zones = get_lxml_element(FARE_ZONES_MISSING_REF)
    result = is_members_scheduled_point_ref_present_in_fare_frame("context", fare_zones)
    assert result == expected