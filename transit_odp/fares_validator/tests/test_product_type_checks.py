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


def get_xml_element(xpath, string_xml):
    doc = etree.fromstring(string_xml)
    elements = doc.xpath(xpath, namespaces=NAMESPACE)
    return elements


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
            "",
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
            "",
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
            "",
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
                else:
                    xml = fare_structure_elements.format(
                        fare_structure_without_time_intervals, product_type_valid_value
                    )
            else:
                xml = fare_structure_elements.format(
                    fare_structure_with_invalid_fare_structure_ref,
                    product_type_valid_value,
                )
        else:
            xml = fare_structure_elements.format(
                fare_structure_fare_structure_ref_not_present, product_type_valid_value
            )
    else:
        xml = fare_structure_elements.format("", product_type_invalid_value)

    xpath = "//x:CompositeFrame/x:frames/x:FareFrame"
    fare_frames = get_xml_element(xpath, xml)
    response = is_fare_structure_element_present("", fare_frames)
    assert response == expected


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
            "",
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
                    else:
                        xml = fare_structure_elements.format(
                            fare_structure_round_trip_not_present,
                            product_type_valid_value,
                        )
                else:
                    xml = fare_structure_elements.format(
                        fare_structure_limitations_not_present, product_type_valid_value
                    )
            else:
                xml = fare_structure_elements.format(
                    fare_structure_generic_parameter_assignment_not_present,
                    product_type_valid_value,
                )
        else:
            xml = fare_structure_elements.format(
                fare_structure_with_invalid_fare_structure_ref,
                product_type_invalid_value,
            )
    else:
        xml = fare_structure_elements.format(
            fare_structure_fare_structure_ref_not_present, ""
        )

    xpath = "//x:CompositeFrame/x:frames/x:FareFrame"
    fare_frames = get_xml_element(xpath, xml)
    response = is_generic_parameter_limitations_present("", fare_frames)
    assert response == expected
