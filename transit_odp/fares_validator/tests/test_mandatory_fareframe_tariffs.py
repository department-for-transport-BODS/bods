import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    check_tariff_basis,
    check_tariff_operator_ref,
    check_tariff_validity_conditions,
    check_type_of_tariff_ref_values,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}
X_PATH = "//x:CompositeFrame/x:frames/x:FareFrame/x:tariffs/x:Tariff"


def get_lxml_element(xpath, string_xml):
    doc = etree.fromstring(string_xml)
    tariffs = doc.xpath(xpath, namespaces=NAMESPACE)
    return tariffs


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "is_type_of_tariff_ref",
        "type_of_tariff_ref_ref_present",
        "type_of_tariff_ref_ref_valid",
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
        (True, False, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            False,
            [
                "violation",
                "9",
                "Mandatory element 'TypeOfTariffRef' is missing in 'Tariff'",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            [
                "violation",
                "10",
                "'TypeOfTariffRef' 'ref' attribute is missing in 'Tariff'",
            ],
        ),
        (
            True,
            True,
            True,
            True,
            False,
            ["violation", "10", "'TypeOfTariffRef' has unexpected value"],
        ),
    ],
)
def test_check_type_of_tariff_ref_values(
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    is_type_of_tariff_ref,
    type_of_tariff_ref_ref_present,
    type_of_tariff_ref_ref_valid,
    expected,
):
    """
    Test if 'TypeOfTariffRef' element has acceptable 'ref' values
    """
    type_of_tariff_ref_pass = """<TypeOfTariffRef ref="fxc:Distance_kilometers" />"""

    type_of_tariff_ref_ref_not_present = """<TypeOfTariffRef />"""

    type_of_tariff_ref_ref_invalid = """<TypeOfTariffRef ref="fxc:fail" />"""

    type_of_frame_ref_not_present = """<TypeOfFrameRef />"""

    type_of_frame_ref_invalid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />"""

    type_of_frame_ref_valid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""

    tariffs = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:1a_Inbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
                        {0}
                        <tariffs>
                            <Tariff id="Tariff@AdultSingle@Line_1a_Inbound" version="1.0">
                                {1}
                            </Tariff>
                        </tariffs>
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if is_type_of_tariff_ref:
                if type_of_tariff_ref_ref_present:
                    if type_of_tariff_ref_ref_valid:
                        xml = tariffs.format(
                            type_of_frame_ref_valid, type_of_tariff_ref_pass
                        )
                    else:
                        xml = tariffs.format(
                            type_of_frame_ref_valid, type_of_tariff_ref_ref_invalid
                        )
                else:
                    xml = tariffs.format(
                        type_of_frame_ref_valid, type_of_tariff_ref_ref_not_present
                    )
            else:
                xml = tariffs.format(type_of_frame_ref_valid, "")
        else:
            xml = tariffs.format(type_of_frame_ref_invalid, "")
    else:
        xml = tariffs.format(type_of_frame_ref_not_present, "")

    tariffs = get_lxml_element(X_PATH, xml)
    response = check_type_of_tariff_ref_values("", tariffs)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "operator_ref",
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
                "9",
                "Mandatory element 'OperatorRef' is missing in 'Tariff'",
            ],
        ),
    ],
)
def test_check_tariff_operator_ref(
    type_of_frame_ref_ref_present, type_of_frame_ref_ref_valid, operator_ref, expected
):
    """
    Test if 'OperatorRef' element is present
    """
    operator_ref_pass = """<OperatorRef version="1.0" ref="noc:FSYO" />"""

    type_of_frame_ref_not_present = """<TypeOfFrameRef />"""

    type_of_frame_ref_invalid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />"""

    type_of_frame_ref_valid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""

    tariffs = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:1a_Inbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
                        {0}
                        <tariffs>
                            <Tariff id="Tariff@AdultSingle@Line_1a_Inbound" version="1.0">
                                {1}
                            </Tariff>
                        </tariffs>
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if operator_ref:
                xml = tariffs.format(type_of_frame_ref_valid, operator_ref_pass)
            else:
                xml = tariffs.format(type_of_frame_ref_valid, "")
        else:
            xml = tariffs.format(type_of_frame_ref_invalid, "")
    else:
        xml = tariffs.format(type_of_frame_ref_not_present, "")

    tariffs = get_lxml_element(X_PATH, xml)
    response = check_tariff_operator_ref("", tariffs)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "tariff_basis",
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
                "9",
                "Mandatory element 'TariffBasis' is missing in 'Tariff'",
            ],
        ),
    ],
)
def test_check_tariff_basis(
    type_of_frame_ref_ref_present, type_of_frame_ref_ref_valid, tariff_basis, expected
):
    """
    Test if 'TariffBasis' is present
    """
    tariff_basis_pass = """<TariffBasis>zoneToZone</TariffBasis>"""

    type_of_frame_ref_not_present = """<TypeOfFrameRef />"""

    type_of_frame_ref_invalid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />"""

    type_of_frame_ref_valid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""

    tariffs = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:1a_Inbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
                        {0}
                        <tariffs>
                            <Tariff id="Tariff@AdultSingle@Line_1a_Inbound" version="1.0">
                                {1}
                            </Tariff>
                        </tariffs>
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if tariff_basis:
                xml = tariffs.format(type_of_frame_ref_valid, tariff_basis_pass)
            else:
                xml = tariffs.format(type_of_frame_ref_valid, "")
        else:
            xml = tariffs.format(type_of_frame_ref_invalid, "")
    else:
        xml = tariffs.format(type_of_frame_ref_not_present, "")

    tariffs = get_lxml_element(X_PATH, xml)
    response = check_tariff_basis("", tariffs)
    assert response == expected


@pytest.mark.parametrize(
    (
        "type_of_frame_ref_ref_present",
        "type_of_frame_ref_ref_valid",
        "validity_conditions",
        "valid_between",
        "from_date",
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
        (True, False, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            False,
            [
                "violation",
                "9",
                "Mandatory element 'validityConditions' is missing in 'Tariff'",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            [
                "violation",
                "10",
                "Mandatory element 'ValidBetween' is missing in 'Tariff.validityConditions'",
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
                "11",
                "Mandatory element 'FromDate' is missing or empty in "
                "'Tariff.validityConditions.ValidBetween'",
            ],
        ),
    ],
)
def test_check_tariff_validity_conditions(
    type_of_frame_ref_ref_present,
    type_of_frame_ref_ref_valid,
    validity_conditions,
    valid_between,
    from_date,
    expected,
):
    """
    Test if 'ValidityConditions', 'ValidBetween' and 'FromDate' are present within 'Tariff'
    """
    tariffs_with_all_children_properties = """<validityConditions>
        <ValidBetween>
            <FromDate>2021-12-22T00:00:00</FromDate>
            <ToDate>2121-12-22T00:00:00</ToDate>
        </ValidBetween>
    </validityConditions>
    """

    tariffs_without_valid_between = """<validityConditions>
    </validityConditions>
    """

    tariffs_without_from_date = """<validityConditions>
        <ValidBetween>
        </ValidBetween>
    </validityConditions>
    """

    type_of_frame_ref_not_present = """<TypeOfFrameRef />"""

    type_of_frame_ref_invalid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_NETW:FXCP" version="fxc:v1.0" />"""

    type_of_frame_ref_valid = """<TypeOfFrameRef ref="fxc:UK:DFT:TypeOfFrame_UK_PI_FARE_PRODUCT:FXCP" version="fxc:v1.0" />"""

    tariffs = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <dataObjects>
            <CompositeFrame id="epd:UK:FYOR:CompositeFrame_UK_PI_LINE_FARE_OFFER:Trip@Line_1_Inbound:op">
                <frames>
                    <FareFrame id="epd:UK:FSYO:FareFrame_UK_PI_FARE_NETWORK:1a_Inbound:op" version="1.0" dataSourceRef="data_source" responsibilitySetRef="network_data">
                        {0}
                        <tariffs>
                            <Tariff id="Tariff@AdultSingle@Line_1a_Inbound" version="1.0">
                                {1}
                            </Tariff>
                        </tariffs>
                    </FareFrame>
                </frames>
            </CompositeFrame>
        </dataObjects>
    </PublicationDelivery>
    """

    if type_of_frame_ref_ref_present:
        if type_of_frame_ref_ref_valid:
            if validity_conditions:
                if valid_between:
                    if from_date:
                        xml = tariffs.format(
                            type_of_frame_ref_valid,
                            tariffs_with_all_children_properties,
                        )
                    else:
                        xml = tariffs.format(
                            type_of_frame_ref_valid, tariffs_without_from_date
                        )
                else:
                    xml = tariffs.format(
                        type_of_frame_ref_valid, tariffs_without_valid_between
                    )
            else:
                xml = tariffs.format(type_of_frame_ref_valid, "")
        else:
            xml = tariffs.format(type_of_frame_ref_invalid, "")
    else:
        xml = tariffs.format(type_of_frame_ref_not_present, "")

    tariffs = get_lxml_element(X_PATH, xml)
    response = check_tariff_validity_conditions("", tariffs)
    assert response == expected
