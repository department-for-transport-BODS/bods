import pytest

from transit_odp.fares_validator.views.functions import (
    is_time_intervals_present_in_tarrifs,
    is_individual_time_interval_present_in_tariffs,
    is_time_interval_name_present_in_tariffs,
)
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

TIME_INTERVALS_OTHER_PRODUCT_TYPE_PASS_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        <ProductType>other</ProductType>
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

TIME_INTERVALS_MISSING_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        <ProductType>dayPass</ProductType>
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

TIME_INTERVALS_REF_MISSING_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef version="fxc:v1.0" />
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        <ProductType>dayPass</ProductType>
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

TIME_INTERVAL_PASS_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
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
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        <ProductType>dayPass</ProductType>
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

TIME_INTERVAL_MISSING_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <timeIntervals>
        </timeIntervals>
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        <ProductType>dayPass</ProductType>
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

TIME_INTERVAL_NAME_MISSING_XML = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <timeIntervals>
        <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day">
            <Name>1 day</Name>
            <Description>P1D</Description>
          </TimeInterval>
          <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day2">
            <Description>P1D</Description>
          </TimeInterval>
        </timeIntervals>
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


def test_time_intervals_pass():
    expected = None
    fare_frames = get_lxml_element(TIME_INTERVALS_PASS_XML)
    result = is_time_intervals_present_in_tarrifs("context", fare_frames)
    assert result == expected


def test_time_intervals_product_type_not_expected_pass():
    expected = None
    fare_frames = get_lxml_element(TIME_INTERVALS_OTHER_PRODUCT_TYPE_PASS_XML)
    result = is_time_intervals_present_in_tarrifs("context", fare_frames)
    assert result == expected


def test_time_intervals_missing():
    expected = ["violation", "5", "Element 'timeIntervals' is missing within 'Tariff'"]
    fare_frames = get_lxml_element(TIME_INTERVALS_MISSING_XML)
    result = is_time_intervals_present_in_tarrifs("context", fare_frames)
    assert result == expected


def test_time_intervals_ref_missing():
    expected = [
        "violation",
        "3",
        "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
    ]
    fare_frames = get_lxml_element(TIME_INTERVALS_REF_MISSING_XML)
    result = is_time_intervals_present_in_tarrifs("context", fare_frames)
    assert result == expected


def test_time_interval_pass():
    expected = None
    fare_frames = get_lxml_element(TIME_INTERVAL_PASS_XML)
    result = is_individual_time_interval_present_in_tariffs("context", fare_frames)
    assert result == expected


def test_time_interval_missing():
    expected = [
        "violation",
        "6",
        "Element 'TimeInterval' is missing within 'timeIntervals'",
    ]
    fare_frames = get_lxml_element(TIME_INTERVAL_MISSING_XML)
    result = is_individual_time_interval_present_in_tariffs("context", fare_frames)
    assert result == expected


def test_time_interval_missing_ref():
    expected = [
        "violation",
        "3",
        "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
    ]
    fare_frames = get_lxml_element(TIME_INTERVALS_REF_MISSING_XML)
    result = is_individual_time_interval_present_in_tariffs("context", fare_frames)
    assert result == expected


def test_time_interval_name_pass():
    expected = None
    fare_frames = get_lxml_element(TIME_INTERVAL_PASS_XML)
    result = is_time_interval_name_present_in_tariffs("context", fare_frames)
    assert result == expected


def test_time_interval_name_missing():
    expected = ["violation", "11", "Element 'Name' is missing within 'TimeInterval'"]
    fare_frames = get_lxml_element(TIME_INTERVAL_NAME_MISSING_XML)
    result = is_time_interval_name_present_in_tariffs("context", fare_frames)
    assert result == expected


def test_time_interval_name_missing_ref():
    expected = [
        "violation",
        "3",
        "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
    ]
    fare_frames = get_lxml_element(TIME_INTERVALS_REF_MISSING_XML)
    result = is_time_interval_name_present_in_tariffs("context", fare_frames)
    assert result == expected
