import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    is_fare_structure_element_present,
    is_generic_parameter_limitations_present,
    is_individual_time_interval_present_in_tariffs,
    is_time_interval_name_present_in_tariffs,
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


@pytest.mark.parametrize(
    (
        "product_type_valid",
        "type_of_fare_structure_element_ref_present",
        "type_of_fare_structure_element_ref_valid",
        "time_intervals",
        "time_interval_ref",
        "expected",
    ),
    [
        (True, True, True, True, True, None),
        (False, False, False, False, False, None),
        (
            True,
            False,
            False,
            False,
            False,
            [
                "violation",
                "13",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (True, True, False, False, False, None),
        (
            True,
            True,
            True,
            False,
            False,
            [
                "violation",
                "11",
                "Element 'timeIntervals' is missing within 'FareStructureElement'",
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
                "14",
                "Element 'TimeIntervalRef' is missing or empty within 'timeIntervals'",
            ],
        ),
    ],
)
def test_is_fare_structure_element_present(
    product_type_valid,
    type_of_fare_structure_element_ref_present,
    type_of_fare_structure_element_ref_valid,
    time_intervals,
    time_interval_ref,
    expected,
):
    """
    Test if ProductType is dayPass or periodPass.
    If true, FareStructureElement elements
    should be present in Tariff.FareStructureElements
    """
    actual = None

    fare_structure_with_all_children_properties = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <Name>O/D pairs for Line 9 Outbound</Name>
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <timeIntervals>
            <TimeIntervalRef version="1.0" ref="op:Tariff@Sheffield_CityBus_1_Day@1-day"/>
            <TimeIntervalRef version="1.0" ref="op:Tariff@Sheffield_CityBus_1_Day@1-day3"/>
        </timeIntervals>
    </FareStructureElement>
    """

    fare_structure_without_time_interval_ref = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <Name>O/D pairs for Line 9 Outbound</Name>
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <timeIntervals>
        </timeIntervals>
    </FareStructureElement>
    """

    fare_structure_without_time_intervals = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <Name>O/D pairs for Line 9 Outbound</Name>
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
    </FareStructureElement>
    """

    fare_structure_with_invalid_fare_structure_ref = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <Name>O/D pairs for Line 9 Outbound</Name>
        <TypeOfFareStructureElementRef ref="fxc:distance_kilometers" version="fxc:v1.0" />
    </FareStructureElement>
    """

    fare_structure_fare_structure_ref_not_present = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <Name>O/D pairs for Line 9 Outbound</Name>
        <TypeOfFareStructureElementRef />
    </FareStructureElement>
    """

    product_type_valid_value = """
    <ProductType>dayPass</ProductType>
    """

    product_type_invalid_value = """
    <ProductType>singlePass</ProductType>
    """

    fare_structure_elements = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:SPSV:FareFrame_UK_PI_FARE_PRODUCT:SPSV:PK1007823:51:236@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
                        <tariffs>
                            <Tariff version="1.0" id="Tariff@single@SPSV:PK1007823:51:236">
                                <fareStructureElements>
                                    {0}
                                </fareStructureElements>
                            </Tariff>
                        </tariffs>
                        <fareProducts>
                            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                                {1}
                            </PreassignedFareProduct>
                        </fareProducts>
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if product_type_valid:
        if type_of_fare_structure_element_ref_present:
            if type_of_fare_structure_element_ref_valid:
                if time_intervals:
                    if time_interval_ref:
                        xml = fare_structure_elements.format(
                            fare_structure_with_all_children_properties,
                            product_type_valid_value,
                        )
                    else:
                        xml = fare_structure_elements.format(
                            fare_structure_without_time_interval_ref,
                            product_type_valid_value,
                        )
                        actual = [
                            "violation",
                            "14",
                            "Element 'TimeIntervalRef' is missing or empty within 'timeIntervals'",
                        ]
                else:
                    xml = fare_structure_elements.format(
                        fare_structure_without_time_intervals, product_type_valid_value
                    )
                    actual = [
                        "violation",
                        "11",
                        "Element 'timeIntervals' is missing within 'FareStructureElement'",
                    ]
            else:
                xml = fare_structure_elements.format(
                    fare_structure_with_invalid_fare_structure_ref,
                    product_type_valid_value,
                )
        else:
            xml = fare_structure_elements.format(
                fare_structure_fare_structure_ref_not_present, product_type_valid_value
            )
            actual = [
                "violation",
                "13",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ]
    else:
        xml = fare_structure_elements.format("", product_type_invalid_value)

    netex_xml = etree.fromstring(xml)
    xpath = "//x:CompositeFrame/x:frames/x:FareFrame"
    fare_frames = netex_xml.xpath(
        xpath, namespaces={"x": "http://www.netex.org.uk/netex"}
    )

    response = is_fare_structure_element_present("", fare_frames)
    print("response ", response)
    if response:
        assert actual == expected


@pytest.mark.parametrize(
    (
        "type_of_fare_structure_element_ref_present",
        "product_type_and_type_of_fare_structure_element_ref_valid",
        "generic_parameter_assigmment",
        "limitations",
        "round_trip",
        "trip_type",
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
                "13",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (True, False, False, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            False,
            False,
            [
                "violation",
                "11",
                "Mandatory element 'FareStructureElement.GenericParameterAssignment'"
                " and it's child elements is missing",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            False,
            [
                "violation",
                "14",
                "Mandatory element 'FareStructureElement.GenericParameterAssignment."
                "limitations' is missing",
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
                "17",
                "Element 'RoundTrip' is missing within ''limitations''",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            True,
            False,
            ["violation", "18", "Element 'TripType' is missing within 'RoundTrip'"],
        ),
    ],
)
def test_is_generic_parameter_limitations_present(
    type_of_fare_structure_element_ref_present,
    product_type_and_type_of_fare_structure_element_ref_valid,
    generic_parameter_assigmment,
    limitations,
    round_trip,
    trip_type,
    expected,
):
    """
    Test if ProductType is singleTrip, dayReturnTrip, periodReturnTrip.
    If true, FareStructureElement.GenericParameterAssignment elements
    should be present in Tariff.FareStructureElements
    """
    actual = None

    fare_structure_with_all_children_properties = """
    <FareStructureElement version="1.0" id="Tariff@single@conditions_of_travel">
        <Name>Conditions of travel</Name>
        <TypeOfFareStructureElementRef versionRef="fxc:v1.0" ref="fxc:travel_conditions"/>
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@single@conditions_of_travel">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use"/>
            <LimitationGroupingType>AND</LimitationGroupingType>
            <limitations>
                <RoundTrip version="1.0" id="Tariff@single@condition@direction">
                    <Name>Single Trip</Name>
                    <TripType>single</TripType>
                </RoundTrip>
            </limitations>
        </GenericParameterAssignment>
    </FareStructureElement>
    """

    fare_structure_fare_structure_ref_not_present = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <Name>Conditions of travel</Name>
        <TypeOfFareStructureElementRef />
    </FareStructureElement>
    """

    fare_structure_with_invalid_fare_structure_ref = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <Name>Conditions of travel</Name>
        <TypeOfFareStructureElementRef versionRef="fxc:v1.0" ref="fxc:eligibility"/>
    </FareStructureElement>
    """

    fare_structure_generic_parameter_assignment_not_present = """
    <FareStructureElement version="1.0" id="Tariff@single@conditions_of_travel">
        <Name>Conditions of travel</Name>
        <TypeOfFareStructureElementRef versionRef="fxc:v1.0" ref="fxc:travel_conditions"/>
    </FareStructureElement>
    """

    fare_structure_limitations_not_present = """
    <FareStructureElement version="1.0" id="Tariff@single@conditions_of_travel">
        <Name>Conditions of travel</Name>
        <TypeOfFareStructureElementRef versionRef="fxc:v1.0" ref="fxc:travel_conditions"/>
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@single@conditions_of_travel">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use"/>
            <LimitationGroupingType>AND</LimitationGroupingType>
        </GenericParameterAssignment>
    </FareStructureElement>
    """

    fare_structure_round_trip_not_present = """
    <FareStructureElement version="1.0" id="Tariff@single@conditions_of_travel">
        <Name>Conditions of travel</Name>
        <TypeOfFareStructureElementRef versionRef="fxc:v1.0" ref="fxc:travel_conditions"/>
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@single@conditions_of_travel">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use"/>
            <LimitationGroupingType>AND</LimitationGroupingType>
            <limitations>
            </limitations>
        </GenericParameterAssignment>
    </FareStructureElement>
    """

    fare_structure_trip_type_not_present = """
    <FareStructureElement version="1.0" id="Tariff@single@conditions_of_travel">
        <Name>Conditions of travel</Name>
        <TypeOfFareStructureElementRef versionRef="fxc:v1.0" ref="fxc:travel_conditions"/>
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@single@conditions_of_travel">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use"/>
            <LimitationGroupingType>AND</LimitationGroupingType>
            <limitations>
                <RoundTrip version="1.0" id="Tariff@single@condition@direction">
                    <Name>Single Trip</Name>
                </RoundTrip>
            </limitations>
        </GenericParameterAssignment>
    </FareStructureElement>
    """

    product_type_valid_value = """
    <ProductType>singleTrip</ProductType>
    """

    product_type_invalid_value = """
    <ProductType>fail</ProductType>
    """

    fare_structure_elements = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame version="1.0" id="epd:UK:SPSV:FareFrame_UK_PI_FARE_PRODUCT:SPSV:PK1007823:51:236@pass:op" dataSourceRef="op:operator" responsibilitySetRef="op:tariffs">
                        <tariffs>
                            <Tariff version="1.0" id="Tariff@single@SPSV:PK1007823:51:236">
                                <fareStructureElements>
                                    {0}
                                </fareStructureElements>
                            </Tariff>
                        </tariffs>
                        <fareProducts>
                            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                                {1}
                            </PreassignedFareProduct>
                        </fareProducts>
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_fare_structure_element_ref_present:
        if product_type_and_type_of_fare_structure_element_ref_valid:
            if generic_parameter_assigmment:
                if limitations:
                    if round_trip:
                        if trip_type:
                            xml = fare_structure_elements.format(
                                fare_structure_with_all_children_properties,
                                product_type_valid_value,
                            )
                        else:
                            xml = fare_structure_elements.format(
                                fare_structure_trip_type_not_present,
                                product_type_valid_value,
                            )
                            actual = [
                                "violation",
                                "18",
                                "Element 'TripType' is missing within 'RoundTrip'",
                            ]
                    else:
                        xml = fare_structure_elements.format(
                            fare_structure_round_trip_not_present,
                            product_type_valid_value,
                        )
                        actual = [
                            "violation",
                            "17",
                            "Element 'RoundTrip' is missing within ''limitations''",
                        ]
                else:
                    xml = fare_structure_elements.format(
                        fare_structure_limitations_not_present, product_type_valid_value
                    )
                    actual = [
                        "violation",
                        "14",
                        "Mandatory element 'FareStructureElement."
                        "GenericParameterAssignment.limitations' is missing",
                    ]
            else:
                xml = fare_structure_elements.format(
                    fare_structure_generic_parameter_assignment_not_present,
                    product_type_valid_value,
                )
                actual = [
                    "violation",
                    "11",
                    "Mandatory element 'FareStructureElement.GenericParameter"
                    "Assignment' and it's child elements is missing",
                ]
        else:
            xml = fare_structure_elements.format(
                fare_structure_with_invalid_fare_structure_ref,
                product_type_invalid_value,
            )
    else:
        xml = fare_structure_elements.format(
            fare_structure_fare_structure_ref_not_present, ""
        )
        actual = [
            "violation",
            "13",
            "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
        ]

    netex_xml = etree.fromstring(xml)
    xpath = "//x:CompositeFrame/x:frames/x:FareFrame"
    fare_frames = netex_xml.xpath(
        xpath, namespaces={"x": "http://www.netex.org.uk/netex"}
    )

    response = is_generic_parameter_limitations_present("", fare_frames)
    print("response ", response)
    if response:
        assert actual == expected
