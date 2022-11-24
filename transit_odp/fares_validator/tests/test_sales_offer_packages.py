import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    check_sales_offer_package,
    check_dist_assignments,
    check_sale_offer_package_elements,
    check_payment_methods,
    check_fare_product_ref,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}


def get_lxml_element(xpath, string_xml):
    doc = etree.fromstring(string_xml)
    fare_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_frames


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "type_of_frame_ref_correct",
        "sales_offer_packages_present",
        "sales_offer_package_present",
        "expected",
    ),
    [
        (True, True, True, True, None),
        (
            False,
            False,
            True,
            True,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            False,
            True,
            True,
            True,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            True,
            False,
            False,
            False,
            None,
        ),
        (
            True,
            True,
            False,
            True,
            [
                "violation",
                "5",
                "'salesOfferPackages' and it's child elements is missing from 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            [
                "violation",
                "8",
                "'salesOfferPackage' and it's child elements is missing from 'salesOfferPackages' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_check_sales_offer_package(
    type_of_frame_ref_present,
    type_of_frame_ref_correct,
    sales_offer_packages_present,
    sales_offer_package_present,
    expected,
):
    sales_offer_packages = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
        <salesOfferPackageElements>
          <SalesOfferPackageElement id="Trip@AdultSingle-SOP@Onboard@printed_ticket" version="1.0" order="1">
            <TypeOfTravelDocumentRef version="fxc:v1.0" ref="fxc:printed_ticket" />
            <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
          </SalesOfferPackageElement>
        </salesOfferPackageElements>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_without_individual_package = """<salesOfferPackages>
    </salesOfferPackages>"""
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""
    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_:FXCP" version="fxc:v1.0" />
    """
    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dataObjects>
    <CompositeFrame version="1.0" id="epd:UK:FSYO:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <frames>
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    {1}
  </FareFrame>
  </frames>
</CompositeFrame>
  </dataObjects>
  </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if type_of_frame_ref_correct:
            if sales_offer_packages_present:
                if sales_offer_package_present:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_present,
                        sales_offer_packages,
                    )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_present,
                        sales_offer_packages_without_individual_package,
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    "",
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_incorrect,
                "",
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            sales_offer_packages,
        )
    sales_offer_package = get_lxml_element(
        "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame", xml
    )
    result = check_sales_offer_package("", sales_offer_package)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "type_of_frame_ref_correct",
        "sales_dist_assignments_present",
        "sales_dist_assignment_present",
        "sales_dict_assignment_channel_type_present",
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
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            False,
            True,
            True,
            True,
            True,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            True,
            False,
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
                "9",
                "'distributionAssignments' and it's child elements is missing from 'salesOfferPackage' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            True,
            [
                "violation",
                "12",
                "'DistributionAssignment' and it's child elements is missing from 'distributionAssignments' in 'FareFrame' - UK_PI_FARE_PRODUCT",
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
                "13",
                "'DistributionChannelType' element is missing or empty from 'DistributionAssignment' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_check_dist_assignments(
    type_of_frame_ref_present,
    type_of_frame_ref_correct,
    sales_dist_assignments_present,
    sales_dist_assignment_present,
    sales_dict_assignment_channel_type_present,
    expected,
):
    sales_offer_packages = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
        <salesOfferPackageElements>
          <SalesOfferPackageElement id="Trip@AdultSingle-SOP@Onboard@printed_ticket" version="1.0" order="1">
            <TypeOfTravelDocumentRef version="fxc:v1.0" ref="fxc:printed_ticket" />
            <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
          </SalesOfferPackageElement>
        </salesOfferPackageElements>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_without_dist_assignments = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_without_dist_assignment = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
        </distributionAssignments>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_without_channel_type = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""
    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_:FXCP" version="fxc:v1.0" />
    """
    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dataObjects>
    <CompositeFrame version="1.0" id="epd:UK:FSYO:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <frames>
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    {1}
  </FareFrame>
  </frames>
</CompositeFrame>
  </dataObjects>
  </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if type_of_frame_ref_correct:
            if sales_dist_assignments_present:
                if sales_dist_assignment_present:
                    if sales_dict_assignment_channel_type_present:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_present,
                            sales_offer_packages,
                        )
                    else:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_present,
                            sales_offer_packages_without_channel_type,
                        )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_present,
                        sales_offer_packages_without_dist_assignment,
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    sales_offer_packages_without_dist_assignments,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_incorrect,
                sales_offer_packages,
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            sales_offer_packages,
        )

    sales_offer_package = get_lxml_element(
        "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame/x:salesOfferPackages/x:SalesOfferPackage",
        xml,
    )
    result = check_dist_assignments("", sales_offer_package)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "type_of_frame_ref_correct",
        "sales_dist_assignment_payment_method_present",
        "expected",
    ),
    [
        (True, True, True, None),
        (
            False,
            False,
            False,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            False,
            True,
            True,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            True,
            False,
            True,
            None,
        ),
        (
            True,
            True,
            False,
            [
                "violation",
                "13",
                "'PaymentMethods' element is missing or empty from 'DistributionAssignment' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_check_payment_methods(
    type_of_frame_ref_present,
    type_of_frame_ref_correct,
    sales_dist_assignment_payment_method_present,
    expected,
):
    sales_offer_packages = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_without_payment_methods = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
          </DistributionAssignment>
        </distributionAssignments>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""
    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_:FXCP" version="fxc:v1.0" />
    """
    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dataObjects>
    <CompositeFrame version="1.0" id="epd:UK:FSYO:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <frames>
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    {1}
  </FareFrame>
  </frames>
</CompositeFrame>
  </dataObjects>
  </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if type_of_frame_ref_correct:
            if sales_dist_assignment_payment_method_present:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    sales_offer_packages,
                )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    sales_offer_packages_without_payment_methods,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_incorrect,
                sales_offer_packages,
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            sales_offer_packages,
        )

    sales_offer_package = get_lxml_element(
        "//x:FareFrame/x:salesOfferPackages/x:SalesOfferPackage/x:distributionAssignments/x:DistributionAssignment",
        xml,
    )
    result = check_payment_methods("", sales_offer_package)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "type_of_frame_ref_correct",
        "sales_offer_element_preassigned_ref_present",
        "expected",
    ),
    [
        (True, True, True, None),
        (
            False,
            False,
            False,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            False,
            True,
            True,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            True,
            False,
            True,
            None,
        ),
        (
            True,
            True,
            False,
            [
                "violation",
                "13",
                "'PreassignedFareProductRef' element is missing from 'SalesOfferPackageElement' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            None,
        ),
    ],
)
def test_check_fare_product_ref(
    type_of_frame_ref_present,
    type_of_frame_ref_correct,
    sales_offer_element_preassigned_ref_present,
    expected,
):
    sales_offer_packages = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <salesOfferPackageElements>
          <SalesOfferPackageElement id="Trip@AdultSingle-SOP@Onboard@printed_ticket" version="1.0" order="1">
            <TypeOfTravelDocumentRef version="fxc:v1.0" ref="fxc:printed_ticket" />
            <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
          </SalesOfferPackageElement>
        </salesOfferPackageElements>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_without_preassigned_ref = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <salesOfferPackageElements>
          <SalesOfferPackageElement id="Trip@AdultSingle-SOP@Onboard@printed_ticket" version="1.0" order="1">
            <TypeOfTravelDocumentRef version="fxc:v1.0" ref="fxc:printed_ticket" />
          </SalesOfferPackageElement>
        </salesOfferPackageElements>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""
    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_:FXCP" version="fxc:v1.0" />
    """
    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dataObjects>
    <CompositeFrame version="1.0" id="epd:UK:FSYO:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <frames>
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    {1}
  </FareFrame>
  </frames>
</CompositeFrame>
  </dataObjects>
  </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if type_of_frame_ref_correct:
            if sales_offer_element_preassigned_ref_present:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    sales_offer_packages,
                )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    sales_offer_packages_without_preassigned_ref,
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_incorrect,
                sales_offer_packages,
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            sales_offer_packages,
        )

    sales_offer_package = get_lxml_element(
        "//x:FareFrame/x:salesOfferPackages/x:SalesOfferPackage/x:salesOfferPackageElements/x:SalesOfferPackageElement",
        xml,
    )
    result = check_fare_product_ref("", sales_offer_package)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_present",
        "type_of_frame_ref_correct",
        "sales_offer_packages_present",
        "sales_offer_package_present",
        "sales_offer_package_elements_present",
        "sales_offer_package_element_present",
        "sales_offer_type_travel_doc_present",
        "expected",
    ),
    [
        (True, True, True, True, True, True, True, None),
        (
            False,
            False,
            True,
            True,
            False,
            False,
            False,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            False,
            True,
            True,
            True,
            True,
            True,
            True,
            [
                "violation",
                "7",
                "'TypeOfFrameRef' 'ref' attribute is missing from 'FareFrame'",
            ],
        ),
        (
            True,
            False,
            True,
            True,
            True,
            True,
            True,
            None,
        ),
        (
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            None,
        ),
        (
            True,
            True,
            True,
            True,
            False,
            True,
            True,
            [
                "violation",
                "9",
                "'salesOfferPackageElements' and it's child elements is missing from 'salesOfferPackage' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            True,
            False,
            True,
            [
                "violation",
                "19",
                "'SalesOfferPackageElement' and it's child elements is missing from 'salesOfferPackageElements' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            True,
            True,
            False,
            [
                "violation",
                "20",
                "'TypeOfTravelDocumentRef' element is missing from 'SalesOfferPackageElement' in 'FareFrame' - UK_PI_FARE_PRODUCT",
            ],
        ),
    ],
)
def test_check_sale_offer_package_elements(
    type_of_frame_ref_present,
    type_of_frame_ref_correct,
    sales_offer_packages_present,
    sales_offer_package_present,
    sales_offer_package_elements_present,
    sales_offer_package_element_present,
    sales_offer_type_travel_doc_present,
    expected,
):
    sales_offer_packages = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
        <salesOfferPackageElements>
          <SalesOfferPackageElement id="Trip@AdultSingle-SOP@Onboard@printed_ticket" version="1.0" order="1">
            <TypeOfTravelDocumentRef version="fxc:v1.0" ref="fxc:printed_ticket" />
            <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
          </SalesOfferPackageElement>
        </salesOfferPackageElements>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_without_individual_package = """ <salesOfferPackages>
    </salesOfferPackages>"""
    sales_offer_packages_without_elements = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
      </SalesOfferPackage>
    </salesOfferPackages>
    """
    sales_offer_packages_without_element = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
        <salesOfferPackageElements>
        </salesOfferPackageElements>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    sales_offer_packages_missing_travel_doc = """<salesOfferPackages>
      <SalesOfferPackage id="Trip@AdultSingle-SOP@Onboard" version="1.0">
        <Name>Onboard</Name>
        <Description>Purchasable on board the bus, with cash or contactless card, as a paper ticket.</Description>
        <distributionAssignments>
          <DistributionAssignment id="Trip@AdultSingle-SOP@Onboard@OnBoard" version="any" order="1">
            <DistributionChannelRef version="fxc:v1.0" ref="fxc:on_board" />
            <DistributionChannelType>onBoard</DistributionChannelType>
            <PaymentMethods>cash contactlessPaymentCard</PaymentMethods>
          </DistributionAssignment>
        </distributionAssignments>
        <salesOfferPackageElements>
          <SalesOfferPackageElement id="Trip@AdultSingle-SOP@Onboard@printed_ticket" version="1.0" order="1">
            <PreassignedFareProductRef version="1.0" ref="Trip@AdultSingle" />
          </SalesOfferPackageElement>
        </salesOfferPackageElements>
      </SalesOfferPackage>
    </salesOfferPackages>"""
    type_of_frame_ref_attr_present = """
    <TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""
    type_of_frame_ref_attr_missing = """
    <TypeOfFrameRef version="fxc:v1.0" />
    """
    type_of_frame_ref_attr_incorrect = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_:FXCP" version="fxc:v1.0" />
    """
    fare_frames = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dataObjects>
    <CompositeFrame version="1.0" id="epd:UK:FSYO:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    <frames>
  <FareFrame version="1.0" id="epd:UK:FSYO:FareFrame_UK_PI_FARE_PRODUCT:Line_9_Outbound:op" dataSourceRef="data_source" responsibilitySetRef="tariffs">
    {0}
    {1}
  </FareFrame>
  </frames>
</CompositeFrame>
  </dataObjects>
  </PublicationDelivery>"""

    if type_of_frame_ref_present:
        if type_of_frame_ref_correct:
            if sales_offer_packages_present:
                if sales_offer_package_present:
                    if sales_offer_package_elements_present:
                        if sales_offer_package_element_present:
                            if sales_offer_type_travel_doc_present:
                                xml = fare_frames.format(
                                    type_of_frame_ref_attr_present,
                                    sales_offer_packages,
                                )
                            else:
                                xml = fare_frames.format(
                                    type_of_frame_ref_attr_present,
                                    sales_offer_packages_missing_travel_doc,
                                )
                        else:
                            xml = fare_frames.format(
                                type_of_frame_ref_attr_present,
                                sales_offer_packages_without_element,
                            )
                    else:
                        xml = fare_frames.format(
                            type_of_frame_ref_attr_present,
                            sales_offer_packages_without_elements,
                        )
                else:
                    xml = fare_frames.format(
                        type_of_frame_ref_attr_present,
                        sales_offer_packages_without_individual_package,
                    )
            else:
                xml = fare_frames.format(
                    type_of_frame_ref_attr_present,
                    "",
                )
        else:
            xml = fare_frames.format(
                type_of_frame_ref_attr_incorrect,
                sales_offer_packages,
            )
    else:
        xml = fare_frames.format(
            type_of_frame_ref_attr_missing,
            sales_offer_packages,
        )
    sales_offer_package = get_lxml_element(
        "//x:dataObjects/x:CompositeFrame/x:frames/x:FareFrame/x:salesOfferPackages/x:SalesOfferPackage",
        xml,
    )
    result = check_sale_offer_package_elements("", sales_offer_package)
    assert result == expected
