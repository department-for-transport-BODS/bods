import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    check_access_right_elements,
    check_fare_products,
    check_fare_products_charging_type,
    check_fare_products_type_ref,
    check_fare_product_validable_elements,
    check_product_type,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}
X_PATH = "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame/x:fareProducts/x:PreassignedFareProduct"


def get_lxml_element(xpath, string_xml):
    doc = etree.fromstring(string_xml)
    elements = doc.xpath(xpath, namespaces=NAMESPACE)
    return elements


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "fare_products",
        "fare_product_tag",
        "preassigned_fare_product",
        "name",
        "expected",
    ),
    [
        (True, True, True, "PreassignedFareProduct", True, True, None),
        (
            False,
            False,
            False,
            "PreassignedFareProduct",
            False,
            False,
            "",
        ),
        (True, False, False, "PreassignedFareProduct", False, False, None),
        (
            True,
            True,
            False,
            "PreassignedFareProduct",
            False,
            False,
            [
                "violation",
                "7",
                "'fareProducts' and it's child elements is missing"
                " from 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            "PreassignedFareProduct",
            False,
            False,
            [
                "violation",
                "9",
                "'PreassignedFareProduct' and it's child elements in"
                " 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            "PreassignedFareProduct",
            True,
            False,
            [
                "violation",
                "10",
                "'Name' missing from 'PreassignedFareProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (True, True, True, "AmountOfPriceUnitProduct", True, True, None),
        (
            False,
            False,
            False,
            "AmountOfPriceUnitProduct",
            False,
            False,
            "",
        ),
        (True, False, False, "AmountOfPriceUnitProduct", False, False, None),
        (
            True,
            True,
            False,
            "AmountOfPriceUnitProduct",
            False,
            False,
            [
                "violation",
                "7",
                "'fareProducts' and it's child elements is missing"
                " from 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            "AmountOfPriceUnitProduct",
            False,
            False,
            [
                "violation",
                "9",
                "'PreassignedFareProduct' and it's child elements in"     # in no fare product is present system will throw PreassignedFareProduct error by default
                " 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            "AmountOfPriceUnitProduct",
            True,
            False,
            [
                "violation",
                "10",
                "'Name' missing from 'AmountOfPriceUnitProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_fare_products(
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    fare_products,
    fare_product_tag,
    preassigned_fare_product,
    name,
    expected,
):
    """
    Test if mandatory element 'PreassignedFareProduct' missing in
    fareProducts for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_product_type = "other"
    if fare_product_tag == "AmountOfPriceUnitProduct":
        fare_product_type = "tripCarnet"

    fare_frame_with_all_children_properties = f"""
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <{fare_product_tag} id="Trip@AdultSingle" version="1.0">
                <Name>Adult Single</Name>
                <ProductType>{fare_product_type}</ProductType>
            </{fare_product_tag}>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = f"""
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <{fare_product_tag} id="Trip@AdultSingle" version="1.0">
                <Name>Adult Single</Name>
                <ProductType>{fare_product_type}</ProductType>
            </{fare_product_tag}>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
    </FareFrame>
    """

    fare_frame_without_fare_products = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
    </FareFrame>
    """

    fare_frame_without_preassigned_fare_product = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_name = f"""
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <{fare_product_tag} id="Trip@AdultSingle" version="1.0">
                <ProductType>{fare_product_type}</ProductType>
            </{fare_product_tag}>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if fare_products:
                if preassigned_fare_product:
                    if name:
                        xml = frames.format(fare_frame_with_all_children_properties)
                    else:
                        xml = frames.format(fare_frame_without_name)
                else:
                    xml = frames.format(fare_frame_without_preassigned_fare_product)
            else:
                xml = frames.format(fare_frame_without_fare_products)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    xpath = "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame"
    fare_frames = get_lxml_element(xpath, xml)
    response = check_fare_products("", fare_frames)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "type_of_fare_product",
        "expected",
    ),
    [
        (True, True, True, None),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, None),
        (
            True,
            True,
            False,
            [
                "violation",
                "10",
                "'TypeOfFareProductRef' missing from 'PreassignedFareProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_fare_products_type_ref(
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    type_of_fare_product,
    expected,
):
    """
    Test if mandatory element is 'TypeOfFareProductRef' present
    in PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <TypeOfFareProductRef version="1.0" ref="fxc:standard_product@trip@single"/>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <TypeOfFareProductRef version="1.0" ref="fxc:standard_product@trip@single"/>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_type_of_fare_product_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if type_of_fare_product:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_type_of_fare_product_ref)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH, xml)
    response = check_fare_products_type_ref("", preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "charging_moment_type",
        "expected",
    ),
    [
        (True, True, True, None),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, None),
        (
            True,
            True,
            False,
            [
                "violation",
                "10",
                "'ChargingMomentType' missing from 'PreassignedFareProduct'"
                " in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_fare_products_charging_type(
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    charging_moment_type,
    expected,
):
    """
    Test if mandatory element is 'ChargingMomentType' present in
    PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ChargingMomentType>beforeTravel</ChargingMomentType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ChargingMomentType>beforeTravel</ChargingMomentType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_charging_moment_type = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if charging_moment_type:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_charging_moment_type)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH, xml)
    response = check_fare_products_charging_type(
        "", preassigned_fare_products
    )
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "validable_elements",
        "validable_element",
        "fare_structure_elements",
        "fare_structure_element_ref",
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
                "10",
                "'validableElements' and it's child elements missing from "
                "'PreassignedFareProduct' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
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
                "11",
                "'ValidableElement' missing from 'PreassignedFareProduct'"
                " in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
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
                "12",
                "'fareStructureElements' and it's child elements missing from "
                "'PreassignedFareProduct' in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            True,
            False,
            [
                "violation",
                "14",
                "'FareStructureElementRef' missing from 'PreassignedFareProduct' "
                "in 'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_preassigned_validable_elements(
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    validable_elements,
    validable_element,
    fare_structure_elements,
    fare_structure_element_ref,
    expected,
):
    """
    Test if element 'validableElements' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    <fareStructureElements>
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access" />
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@conditions_of_travel" />
                        <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access_when" />
                    </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                        <Name>Adult Single</Name>
                        <fareStructureElements>
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access" />
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@conditions_of_travel" />
                            <FareStructureElementRef version="1.0" ref="Tariff@AdultSingle@access_when" />
                        </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_elements = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_element = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_fare_structure_elements = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_fare_structure_element_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <validableElements>
                    <ValidableElement id="Trip@AdultSingle@travel" version="1.0">
                    <Name>Adult Single</Name>
                    <fareStructureElements>
                    </fareStructureElements>
                    </ValidableElement>
                </validableElements>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if validable_elements:
                if validable_element:
                    if fare_structure_elements:
                        if fare_structure_element_ref:
                            xml = frames.format(fare_frame_with_all_children_properties)
                        else:
                            xml = frames.format(
                                fare_frame_without_fare_structure_element_ref
                            )
                    else:
                        xml = frames.format(fare_frame_without_fare_structure_elements)
                else:
                    xml = frames.format(fare_frame_without_validable_element)
            else:
                xml = frames.format(fare_frame_without_validable_elements)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH, xml)
    response = check_fare_product_validable_elements("", preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "access_right",
        "validable_element_ref",
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
        (True, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            [
                "violation",
                "10",
                "'accessRightsInProduct' missing from 'PreassignedFareProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            [
                "violation",
                "12",
                "'ValidableElementRef' missing from 'accessRightsInProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_access_right_elements(
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    access_right,
    validable_element_ref,
    expected,
):
    """
    Test if mandatory element 'AccessRightInProduct' or it's children missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                        <ValidableElementRef version="1.0" ref="Trip@AdultSingle@travel" />
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                        <ValidableElementRef version="1.0" ref="Trip@AdultSingle@travel" />
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_access_rights_in_product = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_validable_element_ref = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <accessRightsInProduct>
                    <AccessRightInProduct id="Trip@AdultSingle@travel@accessRight" version="1.0" order="1">
                    </AccessRightInProduct>
                </accessRightsInProduct>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if access_right:
                if validable_element_ref:
                    xml = frames.format(fare_frame_with_all_children_properties)
                else:
                    xml = frames.format(fare_frame_without_validable_element_ref)
            else:
                xml = frames.format(fare_frame_without_access_rights_in_product)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH, xml)
    response = check_access_right_elements("", preassigned_fare_products)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "product_type",
        "expected",
    ),
    [
        (True, True, True, None),
        (
            False,
            False,
            False,
            "",
        ),
        (True, False, False, None),
        (
            True,
            True,
            False,
            [
                "violation",
                "10",
                "'ProductType' missing or empty from 'PreassignedFareProduct' in "
                "'fareProducts' for 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_product_type(
    type_of_frame_ref_ref_present, type_of_frame_ref_ref_valid, product_type, expected
):
    """
    Test if mandatory element 'ProductType'is missing in
    fareProducts.PreassignedFareProduct for FareFrame - UK_PI_FARE_PRODUCT
    FareFrame UK_PI_FARE_PRODUCT is mandatory
    """
    fare_frame_with_all_children_properties = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ProductType>dayPass</ProductType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_present = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
                <ProductType>dayPass</ProductType>
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_type_of_frame_ref_not_valid = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    fare_frame_without_product_type = """
    <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
        <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />
        <fareProducts>
            <PreassignedFareProduct id="Trip@AdultSingle" version="1.0">
            </PreassignedFareProduct>
        </fareProducts>
    </FareFrame>
    """

    frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    {0}
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if product_type:
                xml = frames.format(fare_frame_with_all_children_properties)
            else:
                xml = frames.format(fare_frame_without_product_type)
        else:
            xml = frames.format(fare_frame_type_of_frame_ref_not_valid)
    else:
        xml = frames.format(fare_frame_type_of_frame_ref_not_present)

    preassigned_fare_products = get_lxml_element(X_PATH, xml)
    response = check_product_type("", preassigned_fare_products)
    assert response == expected
