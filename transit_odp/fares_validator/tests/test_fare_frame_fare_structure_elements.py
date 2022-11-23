import pytest
from lxml import etree

from transit_odp.fares_validator.views.functions import (
    all_fare_structure_element_checks,
    check_fare_structure_element,
    check_frequency_of_use,
    check_generic_parameters_for_access,
    check_generic_parameters_for_eligibility,
    check_type_of_fare_structure_element_ref,
    check_validity_grouping_type_for_access,
    check_validity_parameter_for_access,
)

NAMESPACE = {"x": "http://www.netex.org.uk/netex"}


def get_lxml_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:fareStructureElements"
    service_frames = doc.xpath(xpath, namespaces=NAMESPACE)
    return service_frames


def get_lxml_fare_structure_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = "//x:fareStructureElements/x:FareStructureElement"
    fare_str_elements = doc.xpath(xpath, namespaces=NAMESPACE)
    return fare_str_elements


def get_lxml_generic_param_element(string_xml):
    doc = etree.fromstring(string_xml)
    xpath = (
        "//x:fareStructureElements/x:FareStructureElement/x:GenericParameterAssignment"
    )
    generic_parameter_element = doc.xpath(xpath, namespaces=NAMESPACE)
    return generic_parameter_element


@pytest.mark.parametrize(
    (
        "type_of_fare_str_element_ref_attr_present",
        "type_of_access_right_assig_ref_attr_present",
        "access_fare_structure_absent",
        "eligibility_fare_structure_absent",
        "travel_condition_fare_structure_absent",
        "length_fare_structure_elements_greater_than_two",
        "ref_values_combination_correct",
        "expected",
    ),
    [
        (True, True, False, False, False, True, True, None),
        (
            False,
            True,
            True,
            False,
            False,
            True,
            False,
            [
                "violation",
                "5",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (
            True,
            False,
            False,
            False,
            True,
            True,
            False,
            [
                "violation",
                "5",
                "Attribute 'ref' of element 'TypeOfAccessRightAssignmentRef' is missing",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            False,
            True,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            True,
            False,
            True,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            False,
            True,
            True,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            False,
            False,
            False,
            True,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
        (
            True,
            True,
            False,
            False,
            False,
            True,
            False,
            [
                "violation",
                "5",
                "'FareStructureElement' checks failed: Present at least 3 times, check the 'ref' values are in the correct combination for both 'TypeOfFareStructureElementRef' and 'TypeOfAccessRightAssignmentRef' elements.",
            ],
        ),
    ],
)
def test_all_fare_structure_element_checks(
    type_of_fare_str_element_ref_attr_present,
    type_of_access_right_assig_ref_attr_present,
    access_fare_structure_absent,
    eligibility_fare_structure_absent,
    travel_condition_fare_structure_absent,
    length_fare_structure_elements_greater_than_two,
    ref_values_combination_correct,
    expected,
):
    fare_str_with_children = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    type_of_fare_str_element_attr_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    type_of_access_right_assignment_attr_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0"/>
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_access_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_eligibility_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_travel_conditions_missing = """
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_less_than_three = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_str_incorrect_combination = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            {0}
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if type_of_fare_str_element_ref_attr_present:
        if type_of_access_right_assig_ref_attr_present:
            if not access_fare_structure_absent:
                if not eligibility_fare_structure_absent:
                    if not travel_condition_fare_structure_absent:
                        if length_fare_structure_elements_greater_than_two:
                            if ref_values_combination_correct:
                                xml = fare_frames.format(fare_str_with_children)
                            else:
                                xml = fare_frames.format(fare_str_incorrect_combination)
                        else:
                            xml = fare_frames.format(fare_str_less_than_three)
                    else:
                        xml = fare_frames.format(fare_str_travel_conditions_missing)
                else:
                    xml = fare_frames.format(fare_str_eligibility_missing)
            else:
                xml = fare_frames.format(fare_str_access_missing)
        else:
            xml = fare_frames.format(type_of_access_right_assignment_attr_missing)
    else:
        xml = fare_frames.format(type_of_fare_str_element_attr_missing)

    fare_structure_elements = get_lxml_element(xml)
    result = all_fare_structure_element_checks("", fare_structure_elements)
    assert result == expected


@pytest.mark.parametrize(
    (
        "fare_structure_element_present",
        "expected",
    ),
    [
        (True, None),
        (
            False,
            [
                "violation",
                "5",
                "Mandatory element 'FareStructureElement' is missing",
            ],
        ),
    ],
)
def test_check_fare_structure_element(fare_structure_element_present, expected):
    fare_structure_element = """
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access_when" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:durations" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="01" id="Tariff@AdultSingle@access">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            {0}
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if fare_structure_element_present:
        xml = fare_frames.format(fare_structure_element)
    else:
        xml = fare_frames.format("")
    fare_structure_elements = get_lxml_element(xml)
    result = check_fare_structure_element("", fare_structure_elements)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_fare_structure_element_ref_present",
        "expected",
    ),
    [
        (True, None),
        (
            False,
            [
                "violation",
                "6",
                "Mandatory element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
    ],
)
def test_check_type_of_fare_structure_element_ref(
    type_of_fare_structure_element_ref_present, expected
):
    fare_structure_element = """
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    """
    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement>
                {0}
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if type_of_fare_structure_element_ref_present:
        xml = fare_frames.format(fare_structure_element)
    else:
        xml = fare_frames.format("")
    fare_str_elements = get_lxml_fare_structure_element(xml)
    result = check_type_of_fare_structure_element_ref("", fare_str_elements)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_fare_structure_element_ref_ref_present",
        "ref_value_is_access",
        "generic_parameter_assignment_present",
        "type_of_access_right_assignment_ref_present",
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
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (True, False, True, True, None),
        (
            True,
            True,
            False,
            False,
            [
                "violation",
                "6",
                "Mandatory element 'FareStructureElement.GenericParameterAssignment' and it's child elements is missing",
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
                "Mandatory element 'GenericParameterAssignment.TypeOfAccessRightAssignmentRef' is missing",
            ],
        ),
    ],
)
def test_check_generic_parameters_for_access(
    type_of_fare_structure_element_ref_ref_present,
    ref_value_is_access,
    generic_parameter_assignment_present,
    type_of_access_right_assignment_ref_present,
    expected,
):
    fare_structure_element = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_not_access = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_without_attribute = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_without_generic_child = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
    </FareStructureElement>
    """
    fare_structure_element_without_access_right = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            {0}
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if type_of_fare_structure_element_ref_ref_present:
        if ref_value_is_access:
            if generic_parameter_assignment_present:
                if type_of_access_right_assignment_ref_present:
                    xml = fare_frames.format(fare_structure_element)
                else:
                    xml = fare_frames.format(
                        fare_structure_element_without_access_right
                    )
            else:
                xml = fare_frames.format(fare_structure_element_without_generic_child)
        else:
            xml = fare_frames.format(fare_structure_element_not_access)
    else:
        xml = fare_frames.format(fare_structure_element_without_attribute)
    fare_structure_elements = get_lxml_element(xml)
    result = check_generic_parameters_for_access("", fare_structure_elements)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_fare_structure_element_ref_ref_present",
        "ref_value_is_access",
        "validity_parameter_grouping_type_present",
        "validity_parameter_assignment_type_present",
        "expected",
    ),
    [
        (True, True, True, True, None),
        (True, True, False, True, None),
        (True, True, True, False, None),
        (
            False,
            False,
            True,
            True,
            [
                "violation",
                "7",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (True, False, False, False, None),
        (
            True,
            True,
            False,
            False,
            [
                "violation",
                "8",
                "'ValidityParameterGroupingType' or 'ValidityParameterAssignmentType' elements are missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'",
            ],
        ),
    ],
)
def test_check_validity_grouping_type_for_access(
    type_of_fare_structure_element_ref_ref_present,
    ref_value_is_access,
    validity_parameter_grouping_type_present,
    validity_parameter_assignment_type_present,
    expected,
):
    fare_structure_element_with_grouping = """
    <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
    <ValidityParameterGroupingType>Test</ValidityParameterGroupingType>
    """
    fare_structure_element_with_assignment = """
    <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
    <ValidityParameterAssignmentType>Test</ValidityParameterAssignmentType>
    """
    fare_structure_element_with_both_children = """
    <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
    <ValidityParameterAssignmentType>Test1</ValidityParameterAssignmentType>
    <ValidityParameterGroupingType>Test2</ValidityParameterGroupingType>
    """
    fare_frames_with_access = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
                <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
                <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                    {0}
                </GenericParameterAssignment>
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    fare_frames_not_access = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
                <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
                <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                    {0}
                </GenericParameterAssignment>
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    fare_structure_element_without_attribute = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
                <TypeOfFareStructureElementRef version="fxc:v1.0" />
                <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                    {0}
                </GenericParameterAssignment>
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if type_of_fare_structure_element_ref_ref_present:
        if ref_value_is_access:
            if (
                validity_parameter_grouping_type_present
                and validity_parameter_assignment_type_present
            ):
                xml = fare_frames_with_access.format(
                    fare_structure_element_with_both_children
                )
            elif validity_parameter_grouping_type_present:
                xml = fare_frames_with_access.format(
                    fare_structure_element_with_grouping
                )
            elif validity_parameter_assignment_type_present:
                xml = fare_frames_with_access.format(
                    fare_structure_element_with_assignment
                )
            else:
                xml = fare_frames_with_access.format("")
        else:
            xml = fare_frames_not_access.format("")
    else:
        xml = fare_structure_element_without_attribute.format(
            fare_structure_element_with_both_children
        )
    generic_parameter_frame = get_lxml_generic_param_element(xml)
    result = check_validity_grouping_type_for_access("", generic_parameter_frame)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_fare_structure_element_ref_ref_present",
        "ref_value_is_access",
        "validity_parameter_present",
        "expected",
    ),
    [
        (True, True, True, None),
        (
            False,
            False,
            True,
            [
                "violation",
                "7",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (True, False, False, None),
        (
            True,
            True,
            False,
            [
                "violation",
                "8",
                "'validityParameters' elements are missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a ref value of 'fxc:access'",
            ],
        ),
    ],
)
def test_check_validity_parameter_for_access(
    type_of_fare_structure_element_ref_ref_present,
    ref_value_is_access,
    validity_parameter_present,
    expected,
):
    fare_structure_element_with_child = """
    <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:can_access" />
    <validityParameters>
        <LineRef version="1.0" ref="1_Inbound" />
    </validityParameters>
    """
    fare_frames_with_access = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
                <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
                <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                    {0}
                </GenericParameterAssignment>
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    fare_frames_not_access = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
                <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
                <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                    {0}
                </GenericParameterAssignment>
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    fare_structure_element_without_attribute = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
                <TypeOfFareStructureElementRef version="fxc:v1.0" />
                <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                    {0}
                </GenericParameterAssignment>
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if type_of_fare_structure_element_ref_ref_present:
        if ref_value_is_access:
            if validity_parameter_present:
                xml = fare_frames_with_access.format(fare_structure_element_with_child)
            else:
                xml = fare_frames_with_access.format("")
        else:
            xml = fare_frames_not_access.format("")
    else:
        xml = fare_structure_element_without_attribute.format(
            fare_structure_element_with_child
        )
    generic_parameter_frame = get_lxml_generic_param_element(xml)
    result = check_validity_parameter_for_access("", generic_parameter_frame)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_fare_structure_element_ref_ref_present",
        "ref_value_is_eligibility",
        "generic_parameter_assignment_present",
        "limitation_present",
        "user_profile_prsent",
        "user_profile_children_present",
        "expected",
    ),
    [
        (True, True, True, True, True, True, None),
        (
            False,
            False,
            True,
            True,
            True,
            True,
            [
                "violation",
                "7",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (True, False, True, True, True, True, None),
        (
            True,
            True,
            False,
            False,
            False,
            False,
            [
                "violation",
                "6",
                "Mandatory element 'FareStructureElement.GenericParameterAssignment' and it's child elements is missing",
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
                "8",
                "Mandatory element 'FareStructureElement.GenericParameterAssignment.limitations' is missing",
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
                "10",
                "Mandatory element 'UserProfile' is missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:eligibility'",
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
                "11",
                "Mandatory element 'UserProfile.Name' or 'UserProfile.UserType' is missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:eligibility'",
            ],
        ),
    ],
)
def test_check_generic_parameters_for_eligibility(
    type_of_fare_structure_element_ref_ref_present,
    ref_value_is_eligibility,
    generic_parameter_assignment_present,
    limitation_present,
    user_profile_prsent,
    user_profile_children_present,
    expected,
):
    fare_structure_element = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            <limitations>
                <UserProfile>
                    <Name>Jane Doe</Name>
                    <UserType>Admin</UserType>
                </UserProfile>
            </limitations>
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
            <FareDemandFactorRef version="1.0" ref="op@Tariff@Demand" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_not_eligibility = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_without_attribute = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
                <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_without_generic_child = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
    </FareStructureElement>
    """
    fare_structure_element_without_limitation_child = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
        </GenericParameterAssignment>
    </FareStructureElement>
    <FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_without_user_child = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
                <limitations>
                </limitations>
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_structure_element_without_user_props = """<FareStructureElement id="Tariff@AdultSingle@access" version="1.0">
        <TypeOfFareStructureElementRef ref="fxc:eligibility" version="fxc:v1.0" />
        <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@access_when">
            TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
                <limitations>
                    <UserProfile>
                    </UserProfile>
                </limitations>
        </GenericParameterAssignment>
    </FareStructureElement>
    """
    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            {0}
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>"""
    if type_of_fare_structure_element_ref_ref_present:
        if ref_value_is_eligibility:
            if generic_parameter_assignment_present:
                if limitation_present:
                    if user_profile_prsent:
                        if user_profile_children_present:
                            xml = fare_frames.format(fare_structure_element)
                        else:
                            xml = fare_frames.format(
                                fare_structure_element_without_user_props
                            )
                    else:
                        xml = fare_frames.format(
                            fare_structure_element_without_user_child
                        )
                else:
                    xml = fare_frames.format(
                        fare_structure_element_without_limitation_child
                    )
            else:
                xml = fare_frames.format(fare_structure_element_without_generic_child)
        else:
            xml = fare_frames.format(fare_structure_element_not_eligibility)
    else:
        xml = fare_frames.format(fare_structure_element_without_attribute)
    fare_structure_elements = get_lxml_element(xml)
    result = check_generic_parameters_for_eligibility("", fare_structure_elements)
    assert result == expected


@pytest.mark.parametrize(
    (
        "type_of_fare_structure_element_ref_ref_present",
        "ref_value_is_travel_condition",
        "frequency_of_use_present",
        "frequency_of_use_type_present",
        "expected",
    ),
    [
        (True, True, True, True, None),
        (True, False, True, True, None),
        (
            False,
            False,
            True,
            True,
            [
                "violation",
                "7",
                "Attribute 'ref' of element 'TypeOfFareStructureElementRef' is missing",
            ],
        ),
        (
            True,
            True,
            False,
            True,
            [
                "violation",
                "9",
                "'FrequencyOfUse' is missing from 'GenericParameterAssignment' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:travel_conditions'",
            ],
        ),
        (
            True,
            True,
            True,
            False,
            [
                "violation",
                "10",
                "'FrequencyOfUseType' is missing or empty from 'GenericParameterAssignment.limitations.FrequencyOfUse' when 'TypeOfFareStructureElementRef' has a 'ref' value of 'fxc:travel_conditions'",
            ],
        ),
    ],
)
def test_check_frequency_of_use(
    type_of_fare_structure_element_ref_ref_present,
    ref_value_is_travel_condition,
    frequency_of_use_present,
    frequency_of_use_type_present,
    expected,
):
    fare_structure_element = """<TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
    <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
        <limitations>
            <FrequencyOfUse>
                <FrequencyOfUseType>none</FrequencyOfUseType>
            </FrequencyOfUse>
        </limitations>
        <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
    </GenericParameterAssignment>
    """
    fare_structure_element_not_travel_condition = """<TypeOfFareStructureElementRef ref="fxc:access" version="fxc:v1.0" />
    <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
            <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:eligible" />
    </GenericParameterAssignment>
    """
    fare_structure_element_without_attribute = """<TypeOfFareStructureElementRef version="fxc:v1.0" />
    <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
        <limitations>
            <FrequencyOfUse>
                <FrequencyOfUseType>none</FrequencyOfUseType>
            </FrequencyOfUse>
        </limitations>
        <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
    </GenericParameterAssignment>
    """
    fare_structure_element_without_frequency_of_use = """<TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
    <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
        <limitations>
        </limitations>
        <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
    </GenericParameterAssignment>
    """
    fare_structure_element_without_use_type = """<TypeOfFareStructureElementRef ref="fxc:travel_conditions" version="fxc:v1.0" />
    <GenericParameterAssignment version="1.0" order="1" id="Tariff@AdultSingle@conditions_of_travel">
        <limitations>
            <FrequencyOfUse>
            </FrequencyOfUse>
        </limitations>
        <TypeOfAccessRightAssignmentRef version="fxc:v1.0" ref="fxc:condition_of_use" />
    </GenericParameterAssignment>
    """
    fare_frames = """
    <PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <tariffs>
      <Tariff id="Tariff@AdultSingle@Line_9_Outbound" version="1.0">
        <fareStructureElements>
            <FareStructureElement>
                {0}
            </FareStructureElement>
        </fareStructureElements>
      </Tariff>
    </tariffs>
    </PublicationDelivery>
    """
    if type_of_fare_structure_element_ref_ref_present:
        if ref_value_is_travel_condition:
            if frequency_of_use_present:
                if frequency_of_use_type_present:
                    xml = fare_frames.format(fare_structure_element)
                else:
                    xml = fare_frames.format(fare_structure_element_without_use_type)
            else:
                xml = fare_frames.format(
                    fare_structure_element_without_frequency_of_use
                )
        else:
            xml = fare_frames.format(fare_structure_element_not_travel_condition)
    else:
        xml = fare_frames.format(fare_structure_element_without_attribute)
    fare_structure_elements = get_lxml_fare_structure_element(xml)
    result = check_frequency_of_use("", fare_structure_elements)
    assert result == expected
