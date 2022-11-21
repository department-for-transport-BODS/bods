import pytest

from transit_odp.fares_validator.views.functions import is_uk_pi_fare_price_frame_present
from lxml import etree

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}

FARE_TABLES_PASS_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRICE:FXCP" version="fxc:v1.0" />
      <fareTables>
       <FareTable id="Trip@AdultSingle-SOP@p-ticket@Line_9_Outbound" version="1.0">
        <Name>Sheffield Interchange - Littledale, Mather Rd Outbound</Name>
        <Description>Fares arranged as a fare triangle</Description>
        <pricesFor>
            <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
            <SalesOfferPackageRef version="1.0" ref="Trip@AdultSingle-SOP@Onboard" />
        </pricesFor>
      </FareTable>
    </fareTables>
  </FareFrame>
  </PublicationDelivery>"""

FARE_TABLES_MISSING_FRAME_REF_ATTR_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef version="fxc:v1.0" />
      <fareTables>
       <FareTable id="Trip@AdultSingle-SOP@p-ticket@Line_9_Outbound" version="1.0">
        <Name>Sheffield Interchange - Littledale, Mather Rd Outbound</Name>
        <Description>Fares arranged as a fare triangle</Description>
      </FareTable>
    </fareTables>
  </FareFrame>
  </PublicationDelivery>"""

FARE_TABLES_MISSING_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRICE:FXCP" version="fxc:v1.0" />
  </FareFrame>
  </PublicationDelivery>"""

FARE_TABLES_MISSING_FARE_TABLE_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRICE:FXCP" version="fxc:v1.0" />
      <fareTables>
    </fareTables>
  </FareFrame>
  </PublicationDelivery>"""

FARE_TABLES_MISSING_PRICES_FOR_XML ="""<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRICE:FXCP" version="fxc:v1.0" />
      <fareTables>
       <FareTable id="Trip@AdultSingle-SOP@p-ticket@Line_9_Outbound" version="1.0">
        <Name>Sheffield Interchange - Littledale, Mather Rd Outbound</Name>
        <Description>Fares arranged as a fare triangle</Description>
      </FareTable>
    </fareTables>
  </FareFrame>
  </PublicationDelivery>"""


def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:FareFrame"
    fare_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_frames

def test_fare_tables_none_response():
    expected = None
    fare_frames = get_lxml_element(FARE_TABLES_PASS_XML)
    result = is_uk_pi_fare_price_frame_present("context", fare_frames)
    assert result == expected

def test_fare_tables_missing_frame_ref():
    expected = ['violation', '3', "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'"]
    fare_frames = get_lxml_element(FARE_TABLES_MISSING_FRAME_REF_ATTR_XML)
    result = is_uk_pi_fare_price_frame_present("context", fare_frames)
    assert result == expected

def test_fare_tables_missing():
    expected = ['violation', '2', "'fareTables' missing from 'FareFrame' - UK_PI_FARE_PRICE"]
    fare_frames = get_lxml_element(FARE_TABLES_MISSING_XML)
    result = is_uk_pi_fare_price_frame_present("context", fare_frames)
    assert result == expected

def test_fare_tables_missing_fare_table():
    expected = ['violation', '4', "'FareTable' missing from 'fareTables' in 'FareFrame'- UK_PI_FARE_PRICE"]
    fare_frames = get_lxml_element(FARE_TABLES_MISSING_FARE_TABLE_XML)
    result = is_uk_pi_fare_price_frame_present("context", fare_frames)
    assert result == expected

def test_fare_tables_missing_prices_for():
    expected = ['violation', '5', "'PricesFor' missing from 'FareTable' in 'FareFrame'- UK_PI_FARE_PRICE"]
    fare_frames = get_lxml_element(FARE_TABLES_MISSING_PRICES_FOR_XML)
    result = is_uk_pi_fare_price_frame_present("context", fare_frames)
    assert result == expected


