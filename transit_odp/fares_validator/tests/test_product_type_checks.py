import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    is_time_intervals_present_in_tarrifs,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}

TIME_INTERVALS_PASS_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <validityConditions>
          <ValidBetween>
            <FromDate>2021-12-22T00:00:00</FromDate>
            <ToDate>2121-12-22T00:00:00</ToDate>
          </ValidBetween>
        </validityConditions>
        <Name>First South Yorkshire 9 Outbound - Adult Single fares</Name>
        <OperatorRef version="1.0" ref="noc:FSYO" />
        <LineRef ref="9_Outbound" version="1.0" />
        <TypeOfTariffRef version="fxc:v1.0" ref="fxc:zonal"/>
        <TariffBasis>zoneToZone</TariffBasis>
        <timeIntervals>
          <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day">
            <Name>1 day</Name>
            <Description>P1D</Description>
          </TimeInterval>
          <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day2">
            <Name>2 day</Name>
            <Description>P1D</Description>
          </TimeInterval>
        </timeIntervals>
        <fareStructureElements>
          <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
            <Name>O/D pairs for Line 9 Outbound</Name>
            <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
            <timeIntervals>
                <TimeIntervalRef version="1.0" ref="op:Tariff@Sheffield_CityBus_1_Day@1"/>
            </timeIntervals>
          </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        <ProductType>dayPass</ProductType>
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""


def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:FareFrame"
    fare_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_frames


def test_time_intervals_none_response():
    expected = None
    fare_frames = get_lxml_element(TIME_INTERVALS_PASS_XML)
    result = is_time_intervals_present_in_tarrifs("context", fare_frames)
    assert result == expected
