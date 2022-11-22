import pytest

from transit_odp.fares_validator.views.functions import (
    is_time_intervals_present_in_tarrifs,
    is_individual_time_interval_present_in_tariffs,
    is_time_interval_name_present_in_tariffs,
)
from lxml import etree

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}


def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:FareFrame"
    fare_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_frames


@pytest.mark.parametrize(
    (
        "product_type_valid",
        "time_intervals_present",
        "type_of_frame_ref_present",
        "expected",
    ),
    [
        (True, True, True, None),
        (False, False, False, None),
        (
            True,
            False,
            True,
            ["violation", "8", "Element 'timeIntervals' is missing within 'Tariff'"],
        ),
        (
            True,
            True,
            False,
            [
                "violation",
                "5",
                "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
            ],
        ),
        (
            False,
            True,
            True,
            None,
        ),
    ],
)
def test_is_time_intervals_present_in_tarrifs(
    product_type_valid, time_intervals_present, type_of_frame_ref_present, expected
):

    time_intervals = """
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
    """

    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    """
    product_type_valid_value = """
    <ProductType>dayPass</ProductType>
    """
    product_type_invalid_value = """
    <ProductType>singlePass</ProductType>
    """

    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        {1}
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        {2}
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

    if product_type_valid:
        if time_intervals_present:
            if type_of_frame_ref_present:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    time_intervals,
                    product_type_valid_value,
                )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_missing,
                    time_intervals,
                    product_type_valid_value,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_present, "", product_type_valid_value
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_present, time_intervals, product_type_invalid_value
        )

    fare_frames = get_lxml_element(xml)
    result = is_time_intervals_present_in_tarrifs("", fare_frames)
    assert result == expected


@pytest.mark.parametrize(
    (
        "product_type_valid",
        "time_interval_present",
        "type_of_frame_ref_present",
        "expected",
    ),
    [
        (True, True, True, None),
        (False, False, False, None),
        (
            True,
            False,
            True,
            [
                "violation",
                "9",
                "Element 'TimeInterval' is missing within 'timeIntervals'",
            ],
        ),
        (
            True,
            True,
            False,
            [
                "violation",
                "5",
                "Attribute 'ref' of element 'TypeOfFrameRef' is missing",
            ],
        ),
        (
            False,
            True,
            True,
            None,
        ),
    ],
)
def test_is_individual_time_interval_present_in_tariffs(
    product_type_valid, time_interval_present, type_of_frame_ref_present, expected
):

    time_interval = """
      <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day">
        <Name>1 day</Name>
        <Description>P1D</Description>
      </TimeInterval>
      <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day2">
        <Name>2 day</Name>
        <Description>P1D</Description>
      </TimeInterval>
    """

    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    """
    product_type_valid_value = """
    <ProductType>dayPass</ProductType>
    """
    product_type_invalid_value = """
    <ProductType>singlePass</ProductType>
    """

    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
      <timeIntervals>
        {1}
      </timeIntervals>
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        {2}
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

    if product_type_valid:
        if time_interval_present:
            if type_of_frame_ref_present:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    time_interval,
                    product_type_valid_value,
                )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_missing,
                    time_interval,
                    product_type_valid_value,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_present, "", product_type_valid_value
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_present, time_interval, product_type_invalid_value
        )

    fare_frames = get_lxml_element(xml)
    result = is_individual_time_interval_present_in_tariffs("", fare_frames)
    assert result == expected


@pytest.mark.parametrize(
    (
        "product_type_valid",
        "time_interval_present",
        "name_present",
        "type_of_frame_ref_present",
        "expected",
    ),
    [
        (True, True, True, True, None),
        (False, False, False, False, None),
        (
            True,
            False,
            True,
            True,
            None,
        ),
        (
            True,
            True,
            False,
            True,
            ["violation", "15", "Element 'Name' is missing within 'TimeInterval'"],
        ),
        (
            False,
            True,
            True,
            True,
            None,
        ),
    ],
)
def test_is_time_interval_name_present_in_tariffs(
    product_type_valid,
    time_interval_present,
    name_present,
    type_of_frame_ref_present,
    expected,
):

    time_interval = """
      <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day">
        <Name>1 day</Name>
        <Description>P1D</Description>
      </TimeInterval>
      <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day2">
        <Name>2 day</Name>
        <Description>P1D</Description>
      </TimeInterval>
    """
    time_interval_name_not_present = """
         <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day">
        <Name>1 day</Name>
        <Description>P1D</Description>
      </TimeInterval>
      <TimeInterval version="1.0" id="op:Tariff@Sheffield_CityBus_1_Day@1-day2">
        <Description>P1D</Description>
      </TimeInterval>
    """
    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    """
    product_type_valid_value = """
    <ProductType>dayPass</ProductType>
    """
    product_type_invalid_value = """
    <ProductType>singlePass</ProductType>
    """

    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
      <timeIntervals>
        {1}
      </timeIntervals>
      </Tariff>
    </tariffs>
    <fareProducts>
      <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
        {2}
      </PreassignedFareProduct>
    </fareProducts>
  </FareFrame>
</PublicationDelivery>"""

    if product_type_valid:
        if time_interval_present:
            if name_present:
                if type_of_frame_ref_present:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_present,
                        time_interval,
                        product_type_valid_value,
                    )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_missing,
                        time_interval,
                        product_type_valid_value,
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    time_interval_name_not_present,
                    product_type_valid_value,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_present, "", product_type_invalid_value
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_present, time_interval, product_type_valid_value
        )

    fare_frames = get_lxml_element(xml)
    result = is_time_interval_name_present_in_tariffs("", fare_frames)
    assert result == expected
