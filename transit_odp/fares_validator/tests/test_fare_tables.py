import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    is_uk_pi_fare_price_frame_present,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}


def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:FareFrame"
    fare_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_frames


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "fare_tables_present",
        "fare_table_present",
        "fare_table_prices_for_present",
        "expected",
    ),
    [
        (True, True, True, True, None),
        (
            False,
            False,
            False,
            False,
            "",
        ),
        (
            False,
            True,
            True,
            True,
            "",
        ),
        (
            True,
            False,
            True,
            True,
            [
                "violation",
                "2",
                "'fareTables' missing from 'FareFrame' - UK_PI_FARE_PRICE",
            ],
        ),
        (
            True,
            True,
            False,
            True,
            [
                "violation",
                "6",
                "'FareTable' missing from 'fareTables' in 'FareFrame'- UK_PI_FARE_PRICE",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            [
                "violation",
                "7",
                "'PricesFor' missing from 'FareTable' in 'FareFrame'- UK_PI_FARE_PRICE",
            ],
        ),
    ],
)
def test_is_uk_pi_fare_price_frame_present(
    type_of_frame_ref_present,
    fare_tables_present,
    fare_table_present,
    fare_table_prices_for_present,
    expected,
):
    fare_tables = """<fareTables>
       <FareTable id="Trip@AdultSingle-SOP@p-ticket@Line_9_Outbound" version="1.0">
        <Name>Sheffield Interchange - Littledale, Mather Rd Outbound</Name>
        <Description>Fares arranged as a fare triangle</Description>
        <pricesFor>
            <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
            <SalesOfferPackageRef version="1.0" ref="Trip@AdultSingle-SOP@Onboard" />
        </pricesFor>
      </FareTable>
    </fareTables>"""
    fare_tables_without_fare_table = """<fareTables>
    </fareTables>"""
    fare_tables_without_prices_for = """<fareTables>
       <FareTable id="Trip@AdultSingle-SOP@p-ticket@Line_9_Outbound" version="1.0">
        <Name>Sheffield Interchange - Littledale, Mather Rd Outbound</Name>
        <Description>Fares arranged as a fare triangle</Description>
      </FareTable>
    </fareTables>"""
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRICE:FXCP" version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRICE:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
  {0}
  {1}
  </FareFrame>
  </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if fare_tables_present:
            if fare_table_present:
                if fare_table_prices_for_present:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_present,
                        fare_tables,
                    )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_present,
                        fare_tables_without_prices_for,
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present, fare_tables_without_fare_table
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_present,
                "",
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            fare_tables,
        )

    fare_frames = get_lxml_element(xml)
    result = is_uk_pi_fare_price_frame_present("", fare_frames)
    assert result == expected
