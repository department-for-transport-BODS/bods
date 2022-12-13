import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    is_fare_zones_present_in_fare_frame,
    is_members_scheduled_point_ref_present_in_fare_frame,
    is_name_present_in_fare_frame,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}


def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:fareZones"
    fare_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_frames


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "type_of_frame_ref_attr_present",
        "type_of_frame_ref_correct",
        "fare_zones_present",
        "fare_zone_present",
        "expected",
    ),
    [
        (True, True, True, True, True, None),
        (False, False, False, False, False, None),
        (
            False,
            True,
            True,
            True,
            True,
            None,
        ),
        (
            True,
            True,
            False,
            True,
            True,
            [
                "violation",
                "3",
                "Mandatory element 'TypeOfFrameRef' is missing or 'ref' value does not contain 'UK_PI_FARE_NETWORK'",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            True,
            None,
        ),
        (
            True,
            False,
            True,
            True,
            True,
            "",
        ),
        (
            True,
            True,
            True,
            True,
            False,
            ["violation", "5", "Element 'FareZone' is missing within 'fareZones'"],
        ),
    ],
)
def test_is_fare_zones_present_in_fare_frame(
    type_of_frame_ref_present,
    type_of_frame_ref_attr_present,
    type_of_frame_ref_correct,
    fare_zones_present,
    fare_zone_present,
    expected,
):
    fare_zones = """<fareZones>
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
    </fareZones>"""
    fare_zones_without_fare_zone = """<fareZones>
    </fareZones>"""
    type_of_frame_ref_attr_correct = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETWORK:FXCP" version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_missing = """<TypeOfFrameRef version="fxc:v1.0" />"""
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    """
    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    {0}
    {1}
  </FareFrame>
  </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if type_of_frame_ref_attr_present:
            if type_of_frame_ref_correct:
                if fare_zones_present:
                    if fare_zone_present:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_correct,
                            fare_zones,
                        )
                    else:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_correct,
                            fare_zones_without_fare_zone,
                        )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_correct,
                        "",
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_incorrect,
                    fare_zones,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_missing,
                fare_zones,
            )
    else:
        xml = fare_frames.format(
            "",
            fare_zones,
        )
    fare_frames = get_lxml_element(xml)
    result = is_fare_zones_present_in_fare_frame("", fare_frames)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_attr_present",
        "type_of_frame_ref_correct",
        "fare_zone_name_present",
        "fare_zones_present",
        "fare_zone_present",
        "expected",
    ),
    [
        (True, True, True, True, True, None),
        (
            False,
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
            True,
            "",
        ),
        (
            True,
            False,
            True,
            True,
            True,
            [
                "violation",
                "3",
                "Mandatory element 'TypeOfFrameRef' is missing or 'ref' value does not contain 'UK_PI_FARE_NETWORK'",
            ],
        ),
        (
            True,
            True,
            False,
            True,
            True,
            [
                "violation",
                "13",
                "Element 'Name' is missing or empty within the element 'FareZone'",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            True,
            None,
        ),
        (
            True,
            True,
            True,
            True,
            False,
            None,
        ),
    ],
)
def test_is_name_present_in_fare_frame(
    type_of_frame_ref_attr_present,
    type_of_frame_ref_correct,
    fare_zone_name_present,
    fare_zones_present,
    fare_zone_present,
    expected,
):
    fare_zones = """<fareZones>
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
    </fareZones>"""

    fare_zones_without_fare_zone = """<fareZones>
    </fareZones>"""

    fare_zones_without_name = """<fareZones>
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
    </fareZones>"""

    type_of_frame_ref_attr_missing = """<TypeOfFrameRef version="fxc:v1.0" />"""
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_correct = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETWORK:FXCP" version="fxc:v1.0" />
    """

    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    {0}
    {1}
  </FareFrame>
  </PublicationDelivery>"""
    if type_of_frame_ref_attr_present:
        if type_of_frame_ref_correct:
            if fare_zone_name_present:
                if fare_zones_present:
                    if fare_zone_present:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_correct,
                            fare_zones,
                        )
                    else:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_correct,
                            fare_zones_without_fare_zone,
                        )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_correct,
                        "",
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_correct,
                    fare_zones_without_name,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_incorrect,
                fare_zones_without_name,
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            fare_zones_without_name,
        )

    fare_frames = get_lxml_element(xml)
    result = is_name_present_in_fare_frame("", fare_frames)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_attr_present",
        "type_of_frame_ref_correct",
        "fare_zone_members_present",
        "fare_zone_schedule_point_ref_present",
        "fare_zones_present",
        "fare_zone_present",
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
            "",
        ),
        (
            False,
            True,
            True,
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
            True,
            True,
            [
                "violation",
                "3",
                "Mandatory element 'TypeOfFrameRef' is missing or 'ref' value does not contain 'UK_PI_FARE_NETWORK'",
            ],
        ),
        (
            True,
            True,
            False,
            True,
            True,
            True,
            [
                "violation",
                "6",
                "Element 'members' is missing within the element 'FareZone'",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            True,
            True,
            [
                "violation",
                "8",
                "Element 'ScheduledStopPointRef' is missing within the element 'members'",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            False,
            True,
            None,
        ),
        (
            True,
            True,
            True,
            True,
            True,
            False,
            None,
        ),
    ],
)
def test_is_members_scheduled_point_ref_present_in_fare_frame(
    type_of_frame_ref_attr_present,
    type_of_frame_ref_correct,
    fare_zone_members_present,
    fare_zone_schedule_point_ref_present,
    fare_zones_present,
    fare_zone_present,
    expected,
):
    fare_zones = """<fareZones>
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
    </fareZones>"""

    fare_zones_without_fare_zone = """<fareZones>
    </fareZones>"""

    fare_zones_without_members = """<fareZones>
    <FareZone id="fs@0476" version="1.0">
        <Name>Sheffield Interchange</Name>
      </FareZone>
      <FareZone id="fs@0001" version="1.0">
      </FareZone>
    </fareZones>"""

    fare_zones_without_schedule_point_ref = """<fareZones>
      <FareZone id="fs@0476" version="1.0">
        <Name>Sheffield Interchange</Name>
        <members>
        </members>
      </FareZone>
      <FareZone id="fs@0001" version="1.0">
        <Name>12 o'clock court</Name>
        <members>
          <ScheduledStopPointRef ref="atco:370023485" version="any">12 O Clock Court</ScheduledStopPointRef>
        </members>
      </FareZone>
    </fareZones>"""

    type_of_frame_ref_attr_missing = """<TypeOfFrameRef version="fxc:v1.0" />"""
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_correct = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_NETWORK:FXCP" version="fxc:v1.0" />
    """

    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:9_Outbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
    {0}
    {1}
  </FareFrame>
  </PublicationDelivery>"""
    if type_of_frame_ref_attr_present:
        if type_of_frame_ref_correct:
            if fare_zone_members_present:
                if fare_zone_schedule_point_ref_present:
                    if fare_zones_present:
                        if fare_zone_present:
                            xml = fare_frames.format(
                                type_of_frame_ref_attr_correct,
                                fare_zones,
                            )
                        else:
                            xml = fare_frames.format(
                                type_of_frame_ref_attr_correct,
                                fare_zones_without_fare_zone,
                            )
                    else:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_correct,
                            "",
                        )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_correct,
                        fare_zones_without_schedule_point_ref,
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_correct,
                    fare_zones_without_members,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_incorrect,
                fare_zones,
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            fare_zones,
        )

    fare_frames = get_lxml_element(xml)
    result = is_members_scheduled_point_ref_present_in_fare_frame("", fare_frames)
    assert result == expected
